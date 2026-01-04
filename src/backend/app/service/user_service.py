"""
用户服务。

处理注册、登录、登出、Token 缓存、个人资料与设置、登录历史等；封装校验、
安全与 CRUD 编排。
"""

# backend/app/service/user_service.py

from typing import Optional, List, Dict, Any  # 确保导入了所有类型
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

# 隐式绝对导入 (核心依赖)
from crud.crud_user_login_history import crud_login_history
from models.user_login_history import UserLoginHistory
from crud.crud_user_account import crud_user_account
from models.user_account import UserAccount
from core import exceptions
from core.auth import get_password_hash, verify_password, decode_jwt_token  # 补充 decode_jwt_token 供 logout 使用
from core.log import log
from core.exceptions import ValidationException
from redis_client.redis import get_redis
from core.config import config
from service import email_service  # 导入 email_service 模块本身
from schema import user as schemas  # 导入 User Schemas
from redis_client.redis_keys import redis_key_manager
from redis_client.cache_service import cache_service


# ----------------------------------------------------------------------
# 辅助函数 (Service Internal)
# ----------------------------------------------------------------------

async def check_email_exists(db: AsyncSession, email: str) -> bool:
    """
    检查邮箱是否已存在。

    Args:
        db (AsyncSession): 数据库会话。
        email (str): 邮箱地址。

    Returns:
        bool: True 表示已存在。
    """
    log.info(f"Checking email {email} exists")
    existing_user = await crud_user_account.get_by_email(db, email)
    if existing_user:
        return True
    return False


async def check_username_exists(db: AsyncSession, username: str) -> bool:
    """
    检查用户名是否已存在。

    Args:
        db (AsyncSession): 数据库会话。
        username (str): 用户名。

    Returns:
        bool: True 表示已存在。
    """
    existing_user = await crud_user_account.get_by_username(db, username)
    if existing_user:
        return True
    return False


async def service_check_user_exists(db: AsyncSession, username_or_email: str) -> Optional[UserAccount]:
    """
    根据用户名或邮箱查询用户。

    Args:
        db (AsyncSession): 数据库会话。
        username_or_email (str): 用户名或邮箱。

    Returns:
        Optional[UserAccount]: 用户对象或 None。

    Raises:
        exceptions.DatabaseOperationFailedException: 查询异常。
    """
    try:
        user: Optional[UserAccount] = await crud_user_account.get_by_username_or_email(
            db=db, username_or_email=username_or_email
        )
        return user
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("query user")


# ----------------------------------------------------------------------
# 认证与用户注册 (Auth & Registration)
# ----------------------------------------------------------------------

async def service_register_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    code: str
) -> Optional[UserAccount]:
    """
    注册新用户。

    Args:
        db (AsyncSession): 数据库会话。
        username (str): 用户名。
        email (str): 邮箱。
        password (str): 明文密码。
        code (str): 邮箱验证码。

    Returns:
        Optional[UserAccount]: 新建的用户对象。

    Raises:
        exceptions.UsernameHasBeenRegisteredException: 用户名已存在。
        exceptions.DatabaseOperationFailedException: 创建失败。
    """
    log.info(f"Registering user {username}")

    # 验证码验证
    if not await email_service.service_verify_code(email, code):
        raise exceptions.CodeInvalidException()

    # 验证用户名是否存在
    if await check_username_exists(db, username):
        raise exceptions.UsernameHasBeenRegisteredException()

    # 加密密码
    hashed_password = get_password_hash(password)

    # 创建用户账户
    try:
        new_user = await crud_user_account.create(
            db,
            username=username,
            email=email,
            password_hash=hashed_password  # 字段名修正为 password_hash
        )
        return new_user
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("create user")


async def service_login_with_record(
    db: AsyncSession,
    request: Request,
    username: str,
    password: str
) -> Optional[UserAccount]:
    """
    用户登录并记录登录日志。

    Args:
        db (AsyncSession): 数据库会话。
        request (Request): HTTP请求对象。
        username (str): 用户名。
        password (str): 明文密码。

    Returns:
        Optional[UserAccount]: 登录成功的用户对象。

    Raises:
        exceptions.UserNotFoundException: 用户不存在。
        exceptions.PasswordInvalidException: 密码错误。
        exceptions.UserStatusForbiddenException: 用户状态异常。
    """
    # 从请求中获取登录信息
    client_ip = request.client.host
    user_agent = request.headers.get("User-Agent", "")
    device_info = request.headers.get("X-Device-Info", "")
    
    user = await service_check_user_exists(db, username)

    if not user:
        log.info(f"Login failed: user {username} not found")
        
        # 记录登录失败日志
        await create_login_record(
            db=db,
            user_id=None,  # 用户不存在，所以user_id为None
            ip_address=client_ip,
            login_status="failed",
            user_agent=user_agent,
            device_info=device_info,
            failure_reason="User not found"
        )
        
        raise exceptions.UserNotFoundException()

    # 用户状态检查：只有 banned（封禁）状态禁止登录
    # suspended（异常）状态只是标记，用户仍可正常登录，管理员可查看并决定是否封禁
    if user.status == "banned":
        log.error(f"User {user.user_id} is banned, login denied")
        
        # 记录登录失败日志
        await create_login_record(
            db=db,
            user_id=user.user_id,
            ip_address=client_ip,
            login_status="failed",
            user_agent=user_agent,
            device_info=device_info,
            failure_reason="User is banned"
        )
        
        raise exceptions.UserStatusForbiddenException(status=user.status, user_id=user.user_id)
    
    # 如果用户是 suspended 状态，记录日志但允许登录
    if user.status == "suspended":
        log.warning(f"User {user.user_id} is suspended (marked as abnormal), but allowed to login")

    # 密码是否正确
    if not verify_password(password, user.password_hash):
        log.error(f"User {user.user_id} password is invalid")
        
        # 记录登录失败日志
        await create_login_record(
            db=db,
            user_id=user.user_id,
            ip_address=client_ip,
            login_status="failed",
            user_agent=user_agent,
            device_info=device_info,
            failure_reason="Password invalid"
        )
        
        # 管理员账户不受密码错误次数限制
        if user.is_admin:
            log.info(f"Admin user {user.user_id} password invalid, but no failure tracking for admins")
            raise exceptions.PasswordInvalidException(user_id=user.user_id, failed_attempts=0, custom_message="用户名或密码不正确")
        
        # 普通用户：记录密码错误次数，检查是否达到三次阈值
        from core.security import login_failure_tracker, BlacklistManager, ViolationLogger
        fail_count, should_suspend = await login_failure_tracker.record_failed_attempt(user.user_id)
        
        if should_suspend:
            # 密码连续错误3次直接触发标记（不通过累计违规记录）
            # 先标记用户为异常状态
            await BlacklistManager.suspend_user(
                db=db,
                user_id=user.user_id,
                reason=f"连续 {fail_count} 次输错密码，系统自动标记为异常"
            )
            
            # 再记录违规日志（仅用于审计追踪，不触发累计检查）
            await ViolationLogger.log_violation(
                db=db,
                user_id=user.user_id,
                event_type=ViolationLogger.EVENT_MULTIPLE_FAILED_LOGINS,
                event_description=f"连续 {fail_count} 次输错密码，账户被标记为异常",
                risk_level=ViolationLogger.RISK_HIGH,
                ip_address="127.0.0.1",
                auto_check_suspend=False  # 已手动处理标记，跳过累计检查
            )
            await db.commit()
            
            log.warning(f"User {user.user_id} has been suspended due to {fail_count} failed login attempts")
        
        # 根据失败次数确定错误消息
        if fail_count >= 3:
            custom_message = f"密码错误次数过多，账户已被标记为异常，请注意账户安全"
        elif fail_count > 0:
            custom_message = f"用户名或密码不正确，还剩 {3 - fail_count} 次尝试机会"
        else:
            custom_message = "用户名或密码不正确"
        
        raise exceptions.PasswordInvalidException(user_id=user.user_id, failed_attempts=fail_count, custom_message=custom_message)

    # 登录成功，重置密码错误计数（仅普通用户）
    if not user.is_admin:
        from core.security import login_failure_tracker
        await login_failure_tracker.reset_failed_count(user.user_id)

    # 处理旧的未登出会话
    old_login_record = await crud_login_history.get_latest_unlogout_record(db, user.user_id)
    if old_login_record:
        log.info(f"Found old unlogout record {old_login_record.login_id} for user {user.user_id}, forcing logout")
        await crud_login_history.update_logout_info(db, old_login_record)

    # 更新最后登录时间
    try:
        from datetime import datetime, timezone
        updated_user = await crud_user_account.update(
            db,
            user,
            last_login_at=datetime.now(timezone.utc)
        )
        log.info(f"Updated last_login_at for user {user.user_id}")
        user = updated_user
    except SQLAlchemyError as e:
        log.warning(f"Failed to update last_login_at for user {user.user_id}: {e}")
        # 不抛出异常，允许登录继续进行

    # 记录登录成功日志
    await create_login_record(
        db=db,
        user_id=user.user_id,
        ip_address=client_ip,
        login_status="success",
        user_agent=user_agent,
        device_info=device_info,
    )
    
    log.info(f"User {user.user_id} login successfully")
    return user


async def service_save_token_in_redis(token: str) -> bool:
    """
    将 Token 缓存到 Redis。

    Args:
        token (str): 访问 Token。

    Returns:
        bool: 是否缓存成功。
    """
    redis = get_redis()
    if not redis:
        log.warning("Redis connection not available for token storage")
        return False
    
    try:
        key = redis_key_manager.get_token_key(token)
        await redis.set(key, "1", ex=config.jwt.token_expire_time_seconds)
        log.info(f"Save token to redis_client")
        return True
    except Exception as e:
        log.error(f"Error saving token to Redis: {e}")
        # Redis失败时不影响主流程，返回False表示缓存失败但业务可继续
        return False


async def service_set_user_online_status(user_id: int, is_online: bool = True) -> bool:
    """
    设置用户在线状态到 Redis。

    Args:
        user_id (int): 用户 ID。
        is_online (bool): 是否在线。

    Returns:
        bool: 是否设置成功。
    """
    redis = get_redis()
    if redis:
        if is_online:
            # 设置用户在线，过期时间为 token 过期时间的 1.5 倍
            expire_time = int(config.jwt.token_expire_time_seconds * 1.5)
            await redis.set(f"user_online:{user_id}", "1", ex=expire_time)
            log.info(f"Set user {user_id} online status to {is_online}")
        else:
            # 删除在线状态
            await redis.delete(f"user_online:{user_id}")
            log.info(f"Set user {user_id} online status to {is_online}")
        return True
    return False


async def service_get_user_online_status(user_id: int) -> bool:
    """
    获取用户在线状态。

    Args:
        user_id (int): 用户 ID。

    Returns:
        bool: 是否在线。
    """
    redis = get_redis()
    if redis:
        result = await redis.get(f"user_online:{user_id}")
        return result is not None
    return False


async def service_abolish_token_in_redis(token: str) -> bool:
    """
    从 Redis 中删除/废除 Token。

    Args:
        token (str): 访问 Token。

    Returns:
        bool: 是否删除成功。
    """
    redis = get_redis()
    if not redis:
        log.warning("Redis connection not available for token abolition")
        return False
    
    try:
        key = redis_key_manager.get_token_key(token)
        await redis.delete(key)
        log.info(f"Abolish token in redis_client")
        return True
    except Exception as e:
        log.error(f"Error abolishing token in Redis: {e}")
        # Redis失败时不影响主流程，返回False表示删除失败但业务可继续
        return False


async def create_login_record(
    db: AsyncSession,
    user_id: int | None,
    ip_address: str,
    login_status: str,
    user_agent: str | None = None,
    failure_reason: str | None = None,
    device_info: dict | None = None,
) -> UserLoginHistory:
    """
    创建登录记录。

    Args:
        db (AsyncSession): 数据库会话。
        user_id (int | None): 用户 ID。
        ip_address (str): 登录 IP。
        login_status (str): 登录状态。
        user_agent (str | None): UA 字符串。
        failure_reason (str | None): 失败原因。
        device_info (dict | None): 设备信息。

    Returns:
        UserLoginHistory: 新建的登录记录。

    Raises:
        ValidationException: 必填项缺失。
    """
    log.info(f"user_id={user_id}, ip_address={ip_address}, login_status={login_status}")
    if not ip_address or not login_status:
        raise ValidationException("用户ID、IP地址、登录状态不能为空")

    return await crud_login_history.create_login_record(
        db=db,
        user_id=user_id,
        ip_address=ip_address,
        login_status=login_status,
        user_agent=user_agent,
        failure_reason=failure_reason,
        device_info=device_info
    )


async def service_logout(
        db: AsyncSession,
        token: str
) -> bool:
    """
    用户登出。

    Args:
        db (AsyncSession): 数据库会话。
        token (str): 访问 Token。

    Returns:
        bool: 是否登出成功。
    """
    # 从Redis中删除token，使其失效
    if not await service_abolish_token_in_redis(token):
        log.error(f"无法废除Redis中的令牌 {token}")
        # 注意：即使 Redis 删除失败，通常也应该继续记录登出日志

    # 获取用户ID
    log.info(f"Getting user id from token {token}")
    try:
        user_id = decode_jwt_token(token)
    except Exception as e:
        log.error(f"Error decoding token during logout: {e}")
        return False

    # 设置用户离线状态
    await service_set_user_online_status(user_id, is_online=False)

    # 删除用户信息缓存
    cache_key = redis_key_manager.get_user_info_key(user_id)
    await cache_service.delete(cache_key)

    # 查找用户最新的未登出登录记录
    latest_record = await crud_login_history.get_latest_unlogout_record(db, user_id)

    # 增加判空逻辑
    if latest_record:
        log.info(f"Updating logout info for record {latest_record.login_id}")  # 这里访问属性是安全的
        if not latest_record.logout_time:
            await crud_login_history.update_logout_info(db, latest_record)
    else:
        # 如果没找到记录（可能用户从未登录，或者数据被清理），仅记录日志即可，不抛错
        log.warning(f"No active login record found for user {user_id} during logout.")

    log.info(f"User {user_id} logged out successfully")
    return True


async def force_logout_user_sessions(user_id: int) -> bool:
    """
    强制登出用户的所有活跃会话。
    
    此方法用于在封禁用户时，强制使其所有活跃会话失效。

    Args:
        user_id (int): 用户 ID。

    Returns:
        bool: 是否登出成功。
    """
    # 由于当前系统没有存储用户与token的直接映射关系，
    # 我们通过其他方式实现强制登出：
    # 1. 删除用户信息缓存
    cache_key = redis_key_manager.get_user_info_key(user_id)
    await cache_service.delete(cache_key)
    
    # 2. 设置用户为离线状态
    await service_set_user_online_status(user_id, is_online=False)
    
    # 3. 注意：由于token存储在Redis中使用的是token值作为key，我们无法直接通过user_id找到所有token
    # 因此，我们依赖deps.py中的权限检查，当用户状态变为banned时，下次访问会因为状态检查而被拒绝
    log.info(f"User {user_id} has been forced logout from all sessions")
    return True


async def get_current_user(
    db: AsyncSession,
    username_or_email: str,
) -> UserAccount:
    """
    获取当前用户。

    Args:
        db (AsyncSession): 数据库会话。
        username_or_email (str): 用户名或邮箱。

    Returns:
        UserAccount: 用户对象。

    Raises:
        exceptions.UserNotFoundException: 用户不存在。
        exceptions.UserStatusForbiddenException: 用户状态异常。
        exceptions.DatabaseOperationFailedException: 查询失败。
    """
    try:
        user: Optional[UserAccount] = await crud_user_account.get_by_username_or_email(
            db=db, username_or_email=username_or_email
        )
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("query user")

    if not user:
        raise exceptions.UserNotFoundException()

    # 只有 banned 状态禁止访问，suspended 状态可正常使用
    if user.status == "banned":
        raise exceptions.UserStatusForbiddenException(status=user.status)

    return user


# ----------------------------------------------------------------------
# 用户设置模块 (User Settings)
# ----------------------------------------------------------------------

async def get_user_me_service(db: AsyncSession, user_id: int) -> schemas.UserMe:
    """
    获取当前登录用户的详细信息，带缓存。

    Args:
        db (AsyncSession): 数据库会话。
        user_id (int): 用户 ID。

    Returns:
        schemas.UserMe: 用户信息。

    Raises:
        exceptions.UserNotFoundException: 用户不存在。
        exceptions.DatabaseOperationFailedException: 查询失败。
    """
    log.info(f"Fetching profile for user {user_id}")
    
    # 生成缓存键
    cache_key = redis_key_manager.get_user_info_key(user_id)
    
    # 定义从数据库获取用户信息的函数
    async def fetch_user_data():
        log.info(f"Cache miss for user {user_id}, fetching from database")
        user_orm = await crud_user_account.get(db, user_id)
        if not user_orm:
            raise exceptions.UserNotFoundException()
        return schemas.UserMe.model_validate(user_orm)
    
    # 使用缓存服务获取或设置数据，TTL设为300秒
    cache_result = await cache_service.get_or_set(cache_key, fetch_user_data, ttl=300)
    
    # 检查缓存结果是否有效（None 或空字符串都视为无效）
    if cache_result.data is None or cache_result.data == "":
        raise exceptions.UserNotFoundException()
    
    # 确保返回的是UserMe模型对象
    if isinstance(cache_result.data, dict):
        return schemas.UserMe(**cache_result.data)
    
    return cache_result.data


async def update_password_service(
    db: AsyncSession,
    user_id: int,
    password_data: schemas.UserUpdatePassword
) -> schemas.UserMe:
    """
    验证旧密码并更新为新密码。

    Args:
        db (AsyncSession): 数据库会话。
        user_id (int): 用户 ID。
        password_data (schemas.UserUpdatePassword): 密码更新参数。

    Returns:
        schemas.UserMe: 更新后的用户信息。

    Raises:
        exceptions.UserNotFoundException: 用户不存在。
        exceptions.PasswordInvalidException: 旧密码错误。
        exceptions.DatabaseOperationFailedException: 更新失败。
    """
    log.info(f"Updating password for user {user_id}")
    try:
        db_user = await crud_user_account.get(db, user_id)

        if not db_user:
            raise exceptions.UserNotFoundException()

        if not verify_password(password_data.old_password, db_user.password_hash):
            raise exceptions.PasswordInvalidException(user_id=user_id, custom_message="旧密码不正确")

        new_hashed_password = get_password_hash(password_data.new_password)

        updated_orm = await crud_user_account.update(
            db,
            db_user,
            password_hash=new_hashed_password
        )
        
        # 清除用户信息缓存
        cache_key = redis_key_manager.get_user_info_key(user_id)
        await cache_service.delete(cache_key)

        return schemas.UserMe.model_validate(updated_orm)

    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("update password")


async def update_username_service(
    db: AsyncSession,
    user_id: int,
    username_data: schemas.UserUpdateUsername
) -> schemas.UserMe:
    """
    更新用户名并检查唯一性。

    Args:
        db (AsyncSession): 数据库会话。
        user_id (int): 用户 ID。
        username_data (schemas.UserUpdateUsername): 用户名更新参数。

    Returns:
        schemas.UserMe: 更新后的用户信息。

    Raises:
        exceptions.UsernameHasBeenRegisteredException: 用户名重复。
        exceptions.UserNotFoundException: 用户不存在。
        exceptions.DatabaseOperationFailedException: 更新失败。
    """
    log.info(f"Updating username for user {user_id} to {username_data.username}")
    try:
        db_user = await crud_user_account.get(db, user_id)

        if not db_user:
            raise exceptions.UserNotFoundException()

        # 如果用户名没有变化，直接返回
        if db_user.username == username_data.username:
            return schemas.UserMe.model_validate(db_user)

        # 检查新用户名是否已被其他用户使用
        if await check_username_exists(db, username_data.username):
            raise exceptions.UsernameHasBeenRegisteredException()

        updated_orm = await crud_user_account.update(
            db,
            db_user,
            username=username_data.username
        )
        
        # 清除用户信息缓存
        cache_key = redis_key_manager.get_user_info_key(user_id)
        await cache_service.delete(cache_key)

        return schemas.UserMe.model_validate(updated_orm)

    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("update username")


async def update_avatar_service(
    db: AsyncSession,
    user_id: int,
    avatar_data: schemas.UserUpdateAvatar
) -> schemas.UserMe:
    """
    更新用户头像 URL。

    Args:
        db (AsyncSession): 数据库会话。
        user_id (int): 用户 ID。
        avatar_data (schemas.UserUpdateAvatar): 头像更新参数。

    Returns:
        schemas.UserMe: 更新后的用户信息。

    Raises:
        exceptions.UserNotFoundException: 用户不存在。
        exceptions.DatabaseOperationFailedException: 更新失败。
    """
    log.info(f"Updating avatar for user {user_id}")
    try:
        db_user = await crud_user_account.get(db, user_id)
        if not db_user:
            raise exceptions.UserNotFoundException()

        updated_orm = await crud_user_account.update(
            db,
            db_user,
            avatar_url=avatar_data.avatar_url
        )
        
        # 清除用户信息缓存
        cache_key = redis_key_manager.get_user_info_key(user_id)
        await cache_service.delete(cache_key)
        
        return schemas.UserMe.model_validate(updated_orm)
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("update avatar")


async def request_update_email_service(
    db: AsyncSession,
    user_id: int,
    request_data: schemas.UserUpdateEmailRequest
) -> bool:
    """
    检查新邮箱是否可用，并发送验证码。

    Args:
        db (AsyncSession): 数据库会话。
        user_id (int): 用户 ID。
        request_data (schemas.UserUpdateEmailRequest): 邮箱更新请求参数。

    Returns:
        bool: 是否发送成功。

    Raises:
        exceptions.EmailHasBeenRegisteredException: 邮箱已被注册。
        exceptions.DatabaseOperationFailedException: 检查失败。
    """
    log.info(f"User {user_id} requesting email change to {request_data.new_email}")
    try:
        if await check_email_exists(db, request_data.new_email):
            raise exceptions.EmailHasBeenRegisteredException()

        # 2. 调用 Email Service 发送验证码（模拟）
        # await email_service.service_send_email_code(request_data.new_email)
        # 取消注释并且更正函数名
        await email_service.service_send_verification_code(request_data.new_email)
        log.info(f"Verification code sent to {request_data.new_email}")
        return True
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("check email existence")


async def confirm_update_email_service(
    db: AsyncSession,
    user_id: int,
    confirm_data: schemas.UserUpdateEmailConfirm
) -> schemas.UserMe:
    """
    验证验证码并最终更新邮箱。

    Args:
        db (AsyncSession): 数据库会话。
        user_id (int): 用户 ID。
        confirm_data (schemas.UserUpdateEmailConfirm): 邮箱确认参数。

    Returns:
        schemas.UserMe: 更新后的用户信息。

    Raises:
        exceptions.CodeInvalidException: 验证码错误。
        exceptions.UserNotFoundException: 用户不存在。
        exceptions.DatabaseOperationFailedException: 更新失败。
    """
    log.info(f"User {user_id} confirming new email {confirm_data.new_email}")

    # 1. 业务逻辑：校验验证码
    if not await email_service.service_verify_code(confirm_data.new_email, confirm_data.code):
        raise exceptions.CodeInvalidException()

    try:
        db_user = await crud_user_account.get(db, user_id)
        if not db_user:
            raise exceptions.UserNotFoundException()

        # 3. 调用 CRUD 更新邮箱
        updated_orm = await crud_user_account.update(
            db,
            db_user,
            email=confirm_data.new_email
        )
        
        # 清除用户信息缓存
        cache_key = redis_key_manager.get_user_info_key(user_id)
        await cache_service.delete(cache_key)

        return schemas.UserMe.model_validate(updated_orm)
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("confirm and update email")

# 新增添加这个 Service 方法
async def get_login_history_service(
    db: AsyncSession,
    user_id: int,
    page: int,
    page_size: int
) -> schemas.PaginatedLoginHistory:
    """
    获取登录历史分页数据。

    Args:
        db (AsyncSession): 数据库会话。
        user_id (int): 用户 ID。
        page (int): 页码。
        page_size (int): 每页数量。

    Returns:
        schemas.PaginatedLoginHistory: 分页结果。
    """
    # 1. 计算 offset
    skip = (page - 1) * page_size

    # 2. 调用 CRUD 获取数据
    items_orm, total = await crud_login_history.get_multi_by_user(
        db, user_id, skip=skip, limit=page_size
    )

    # 3. 转换为 DTO
    # 注意：LoginHistoryItem 需要在 schema/user.py 中正确定义 (你之前的上传中已经有了)
    items_dto = [schemas.LoginHistoryItem.model_validate(item) for item in items_orm]

    return schemas.PaginatedLoginHistory(
        total=total,
        page=page,
        page_size=page_size,
        items=items_dto
    )
