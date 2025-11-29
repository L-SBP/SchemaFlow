# backend/app/service/user_service.py (完整修正版本)

from typing import Optional, List, Dict, Any  # 确保导入了所有类型
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone  # 导入 timezone 用于日志记录

# 隐式绝对导入 (核心依赖)
from crud.crud_user_login_history import crud_login_history
from models.user_login_history import UserLoginHistory
from crud.crud_user_account import curd_user_account
from models.user_account import UserAccount
from core import exceptions
from core.auth import get_password_hash, verify_password, decode_jwt_token  # 补充 decode_jwt_token 供 logout 使用
from core.log import log
from core.exceptions import ValidationException
from redis.redis import get_redis
from core.config import config
from service import email_service  # 导入 email_service 模块本身
from schema import user as schemas  # 导入 User Schemas


# ----------------------------------------------------------------------
# 辅助函数 (Service Internal)
# ----------------------------------------------------------------------

async def check_email_exists(db: AsyncSession, email: str) -> bool:
    """检查邮箱是否已存在"""
    log.info(f"Checking email {email} exists")
    existing_user = await curd_user_account.get_by_email(db, email)
    if existing_user:
        return True
    return False


async def check_username_exists(db: AsyncSession, username: str) -> bool:
    """检查给定用户名是否已存在"""
    existing_user = await curd_user_account.get_by_username(db, username)
    if existing_user:
        return True
    return False


async def service_check_user_exists(db: AsyncSession, username_or_email: str) -> Optional[UserAccount]:
    """查询用户，用于登录等场景的基础验证"""
    try:
        user: Optional[UserAccount] = await curd_user_account.get_by_username_or_email(
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
    """使用提供的信息注册新用户"""
    log.info(f"Registering user {username}")

    # 验证码验证
    # 假设 email_service.service_verify_code(email, code) 存在
    # if not await email_service.service_verify_code(email, code):
    #     raise exceptions.CodeInvalidException()

    # 验证用户名是否存在
    if await check_username_exists(db, username):
        raise exceptions.UsernameHasBeenRegisteredException()

    # 加密密码
    hashed_password = get_password_hash(password)

    # 创建用户账户
    try:
        new_user = await curd_user_account.create(
            db,
            username=username,
            email=email,
            password_hash=hashed_password  # 字段名修正为 password_hash
        )
        return new_user
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("create user")


async def service_login(
        db: AsyncSession,
        username: str,
        password: str
) -> Optional[UserAccount]:
    """用户登录业务逻辑"""
    user = await service_check_user_exists(db, username)

    if not user:
        log.info(f"Login failed: user {username} not found")
        raise exceptions.UserNotFoundException()

    # 密码是否正确
    if not verify_password(password, user.password_hash):
        log.error(f"User {user.user_id} password is invalid")
        raise exceptions.PasswordInvalidException()

    # 用户状态是否正常
    if user.status != "normal":
        log.error(f"User {user.user_id} status is {user.status}")
        raise exceptions.UserStatusForbiddenException(status=user.status)

    log.info(f"User {user.user_id} login successfully")
    return user


async def service_save_token_in_redis(token: str):
    """Token 缓存到 Redis"""
    redis = get_redis()
    if redis:
        await redis.set(f"token:{token}", "1", ex=config.jwt.token_expire_time_seconds)
        log.info(f"Save token {token} to redis")
        return True
    return False


async def service_abolish_token_in_redis(token: str):
    """Token 从 Redis 中删除/废除"""
    redis = get_redis()
    if redis:
        await redis.delete(f"token:{token}")
        log.info(f"Abolish token {token} in redis")
        return True
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
    """创建登录记录（Router 调用）"""
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
    """用户登出业务逻辑"""
    # 从Redis中删除token，使其失效
    if not await service_abolish_token_in_redis(token):
        log.error(f"Failed to abolish token {token} in redis")
        # 注意：即使 Redis 删除失败，通常也应该继续记录登出日志

    # 获取用户ID
    log.info(f"Getting user id from token {token}")
    try:
        user_id = decode_jwt_token(token)
    except Exception as e:
        log.error(f"Error decoding token during logout: {e}")
        return False

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


async def get_current_user(
        db: AsyncSession,
        username_or_email: str,
) -> UserAccount:
    """获取当前用户业务逻辑"""
    try:
        user: Optional[UserAccount] = await curd_user_account.get_by_username_or_email(
            db=db, username_or_email=username_or_email
        )
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("query user")

    if not user:
        raise exceptions.UserNotFoundException()

    if user.status != "normal":
        raise exceptions.UserStatusForbiddenException(status=user.status)

    return user


# ----------------------------------------------------------------------
# 用户设置模块 (User Settings)
# ----------------------------------------------------------------------

async def get_user_me_service(db: AsyncSession, user_id: int) -> schemas.UserMe:
    """Service 逻辑：获取当前登录用户的详细信息。"""
    log.info(f"Fetching profile for user {user_id}")
    try:
        user_orm = await curd_user_account.get(db, user_id)

        if not user_orm:
            raise exceptions.UserNotFoundException()

        return schemas.UserMe.model_validate(user_orm)

    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("fetch user profile")


async def update_password_service(
        db: AsyncSession,
        user_id: int,
        password_data: schemas.UserUpdatePassword
) -> schemas.UserMe:
    """Service 逻辑：验证旧密码并更新新密码。"""
    log.info(f"Updating password for user {user_id}")
    try:
        db_user = await curd_user_account.get(db, user_id)

        if not db_user:
            raise exceptions.UserNotFoundException()

        if not verify_password(password_data.old_password, db_user.password_hash):
            raise exceptions.PasswordInvalidException("Old password is incorrect.")

        new_hashed_password = get_password_hash(password_data.new_password)

        updated_orm = await curd_user_account.update(
            db,
            db_user,
            password_hash=new_hashed_password
        )

        return schemas.UserMe.model_validate(updated_orm)

    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("update password")


async def update_username_service(
        db: AsyncSession,
        user_id: int,
        username_data: schemas.UserUpdateUsername
) -> schemas.UserMe:
    """Service 逻辑：更新用户名，并检查唯一性。"""
    log.info(f"Updating username for user {user_id} to {username_data.username}")
    try:
        if await check_username_exists(db, username_data.username):
            raise exceptions.UsernameHasBeenRegisteredException()

        db_user = await curd_user_account.get(db, user_id)

        if not db_user:
            raise exceptions.UserNotFoundException()

        updated_orm = await curd_user_account.update(
            db,
            db_user,
            username=username_data.username
        )

        return schemas.UserMe.model_validate(updated_orm)

    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("update username")


async def update_avatar_service(
        db: AsyncSession,
        user_id: int,
        avatar_data: schemas.UserUpdateAvatar
) -> schemas.UserMe:
    """Service 逻辑：更新用户头像 URL。"""
    log.info(f"Updating avatar for user {user_id}")
    try:
        db_user = await curd_user_account.get(db, user_id)
        if not db_user:
            raise exceptions.UserNotFoundException()

        updated_orm = await curd_user_account.update(
            db,
            db_user,
            avatar_url=avatar_data.avatar_url
        )
        return schemas.UserMe.model_validate(updated_orm)
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("update avatar")


async def request_update_email_service(
        db: AsyncSession,
        user_id: int,
        request_data: schemas.UserUpdateEmailRequest
) -> bool:
    """Service 逻辑：检查新邮箱是否可用，并发送验证码。"""
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
    """Service 逻辑：验证验证码，并最终更新邮箱。"""
    log.info(f"User {user_id} confirming new email {confirm_data.new_email}")

    # 1. 业务逻辑：校验验证码
    if not await email_service.service_verify_code(confirm_data.new_email, confirm_data.code):
        raise exceptions.CodeInvalidException()

    try:
        db_user = await curd_user_account.get(db, user_id)
        if not db_user:
            raise exceptions.UserNotFoundException()

        # 3. 调用 CRUD 更新邮箱
        updated_orm = await curd_user_account.update(
            db,
            db_user,
            email=confirm_data.new_email
        )

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
    Service 逻辑：获取登录历史分页数据
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