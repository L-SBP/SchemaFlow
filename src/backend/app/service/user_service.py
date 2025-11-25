from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

import core.auth
from crud.crud_user_login_history import crud_login_history
from models.user_login_history import UserLoginHistory

from crud.crud_user_account import curd_user_account

from models.user_account import UserAccount

from core import exceptions
from core.auth import get_password_hash, verify_password
from core.log import log
from core.exceptions import ValidationException, BusinessException, AppException
from core.redis import get_redis
from core.config import config

from service import email_service


async def check_email_exists(db: AsyncSession, email: str) -> bool:
    """
    检查邮箱是否已存在

    :param db: 数据库会话
    :param email: 要检查的邮箱地址
    :return: 如果邮箱已存在返回True，否则返回False
    """

    log.info(f"Checking email {email} exists")
    existing_user = await curd_user_account.get_by_email(db, email)

    if existing_user:
        return True
    return False

async def check_username_exists(db: AsyncSession, username: str) -> bool:
    """
    检查给定用户名是否已存在
    
    :param db: 数据库会话
    :param username: 要检查的用户名
    :return: 如果用户存在返回True，否则返回False
    """
    existing_user = await curd_user_account.get_by_username(db, username)

    if existing_user:
        return True
    return False

async def service_check_user_exists(db: AsyncSession, username_or_email: str) -> Optional[UserAccount]:
    try:
        user: Optional[UserAccount] = await curd_user_account.get_by_username_or_email(
            db=db, username_or_email=username_or_email
        )
        return user
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("query user")

async def service_register_user(
    db: AsyncSession,
    username: str, 
    email: str, 
    password: str,
    code: str
) -> Optional[UserAccount]:
    """
    使用提供的信息注册新用户
    
    :param db: 数据库会话
    :param username: 用户名
    :param email: 用户邮箱
    :param password: 用户密码（将被哈希处理）
    :param code: 验证码
    :return: 创建的用户账户对象，如果注册失败则返回None
    :raises ValueError: 如果验证失败或用户已存在
    """
    log.info(f"Registering user {username}")
    # 验证code
    if not await email_service.service_verify_code(email, code):
        raise exceptions.CodeInvalidException()
    
    # 验证用户名是否存在
    exists = await check_username_exists(db, username)
    if exists:
        raise exceptions.UsernameHasBeenRegisteredException()

    # 加密密码
    hashed_password = get_password_hash(password)
    
    # 创建用户账户
    try:
        new_user = await curd_user_account.create(
            db,
            username=username,
            email=email,
            password_hash=hashed_password
        )
        return new_user
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("create user")

async def service_login(
        db: AsyncSession,
        username: str,
        password: str
) -> Optional[UserAccount]:
    """
    用户登录业务逻辑：
    1. 根据用户名/邮箱查询用户
    2. 校验用户是否存在
    3. 校验用户状态是否为 normal
    4. 校验密码
    失败则抛业务异常
    
    :param db: 数据库会话
    :param username: user_account数据行
    :param password: 用户密码
    :return: 用户账户对象
    """
    # 查看用户是否存在
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

    # 密码是否正确
    if not verify_password(password, user.password_hash):
        log.error(f"User {user.user_id} password is invalid")
        raise exceptions.PasswordInvalidException()

    log.info(f"User {user.user_id} login successfully")
    return user

async def service_save_token_in_redis(token: str):
    redis = get_redis()
    if redis:
        await redis.set(f"token:{token}", "1", ex=config.jwt.token_expire_time_seconds)
        log.info(f"Save token {token} to redis")
        return True
    return False

async def service_check_token_in_redis(token: str) -> bool:
    redis = get_redis()
    if redis:
        await redis.exists(f"token:{token}")
        log.info(f"Token {token} exists in redis")
        return True
    return False

async def service_abolish_token_in_redis(token: str):
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
    """
    业务逻辑：创建登录记录（校验必填字段）
    
    :param db: 数据库会话
    :param user_id: 用户ID
    :param ip_address: IP地址
    :param login_status: 登录状态
    :param user_agent: 用户代理信息
    :param failure_reason: 失败原因
    :param device_info: 设备信息
    :return: 用户登录历史记录对象
    """
    # 业务校验：必填字段非空
    log.info(f"user_id={user_id}, ip_address={ip_address}, login_status={login_status}")
    if not ip_address or not login_status:
        raise ValidationException("用户ID、IP地址、登录状态不能为空")

    # 调用CRUD层插入数据
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
    业务逻辑：
    1. 从Redis中删除token
    2. 更新用户最新的登录记录为已登出状态
    失败则抛业务异常
    
    :param db: 数据库会话
    :param token: JWT访问令牌
    :return: 登出是否成功
    """
    # 从Redis中删除token，使其失效
    if not await service_abolish_token_in_redis(token):
        log.error(f"Failed to abolish token {token} in redis")
        return False

    # 获取用户ID
    log.info(f"Getting user id from token {token}")
    user_id = core.auth.decode_jwt_token(token)
    
    # 查找用户最新的未登出登录记录
    log.info(f"Getting latest unlogout record for user {user_id}")
    latest_record = await crud_login_history.get_latest_unlogout_record(db, user_id)
    
    # 如果找到记录且尚未登出，则更新登出信息
    log.info(f"Updating logout info for record {latest_record.user_id}")
    if latest_record and not latest_record.logout_time:
        await crud_login_history.update_logout_info(db, latest_record)
    
    log.info(f"User {user_id} logged out successfully")
    return True

async def get_current_user(
        db: AsyncSession,
        username_or_email: str,
) -> UserAccount:
    """
    获取当前用户业务逻辑：
    1. 根据用户名/邮箱查询用户
    2. 校验用户是否存在
    3. 校验用户状态是否为 normal
    失败则抛业务异常
    
    :param db: 数据库会话
    :param username_or_email: 用户名或邮箱
    :return: 用户账户对象
    """
    # 调用 CRUD 层查询用户
    try:
        user: Optional[UserAccount] = await curd_user_account.get_by_username_or_email(
            db=db, username_or_email=username_or_email
        )
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("query user")

    # 用户是否存在
    if not user:
        raise exceptions.UserNotFoundException()

    # 用户状态是否正常
    if user.status != "normal":
        raise exceptions.UserStatusForbiddenException(status=user.status)

    return user