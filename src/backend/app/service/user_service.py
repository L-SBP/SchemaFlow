from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from core.exceptions import BusinessException
from crud.crud_user_login_history import crud_login_history
from models.user_login_history import UserLoginHistory

from crud.crud_user_account import curd_user_account

from models.user_account import UserAccount

from core import exceptions
from core.auth import get_password_hash, verify_password

from core.log import log
from service import email_service


async def check_email_exists(db: AsyncSession, email: str) -> bool:
    """
    Check if email already exists

    Args:
        db: Database session
        email: Email to check

    Returns:
        bool: True if email exists, False otherwise
    """

    log.info(f"Checking email {email} exists")
    existing_user = await curd_user_account.get_by_email(db, email)

    if existing_user:
        return True
    return False

async def check_user_exists(db: AsyncSession, username: str) -> bool:
    """
    Check if user with given username already exists
    
    Args:
        db: Database session
        username: Username to check
        
    Returns:
        tuple: (exists: bool, field: str) - True if user exists, and which field conflicts
    """
    existing_user = await curd_user_account.get_by_username(db, username)

    if existing_user:
        return True
    return False

async def service_register_user(
    db: AsyncSession,
    username: str, 
    email: str, 
    password: str,
    code: str
) -> Optional[UserAccount]:
    """
    Register a new user with the provided information
    
    Args:
        db: Database session
        username: Desired username
        email: User's email
        password: User's password (will be hashed)
        code: Verification code
        
    Returns:
        UserAccount: The created user account, or None if registration failed
        
    Raises:
        ValueError: If verification fails or user already exists
    """
    log.info(f"Registering user {username}")
    # Verify the code
    if not await email_service.verify_code(email, code):
        raise exceptions.CodeInvalidException()
    
    # Check if user already exists
    exists = await check_user_exists(db, username)
    if exists:
        raise exceptions.UsernameHasBeenRegisteredException()

    # Hash the password
    hashed_password = get_password_hash(password)
    
    # Create the user
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
        username_or_email: str,
        password: str
) -> UserAccount:
    """
    业务逻辑：
    1. 根据用户名/邮箱查询用户
    2. 校验用户是否存在
    3. 校验用户状态是否为 normal
    4. 校验密码
    失败则抛业务异常
    """
    # 调用 CRUD 层查询用户
    try:
        user: Optional[UserAccount] = await curd_user_account.get_by_username_or_email(
            db=db, username_or_email=username_or_email
        )
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("query user")

    #  业务校验 1：用户是否存在
    if not user:
        log.error(f"User {username_or_email} not found")
        raise exceptions.UserNotFoundException()

    # 业务校验 2：用户状态是否正常
    if user.status != "normal":
        log.error(f"User {username_or_email} status is {user.status}")
        raise exceptions.UserStatusForbiddenException(status=user.status)

    # 业务校验 3：密码是否正确
    if not verify_password(password, user.password_hash):
        log.error(f"User {username_or_email} password is invalid")
        raise exceptions.PasswordInvalidException()

    log.info(f"User {username_or_email} login successfully")
    return user


async def create_login_record(
        db: AsyncSession,
        user_id: int,
        ip_address: str,
        login_status: str,
        user_agent: str | None = None,
        failure_reason: str | None = None,
        device_info: dict | None = None,
) -> UserLoginHistory:
    """
    业务逻辑：创建登录记录（校验必填字段）
    """
    # 业务校验：必填字段非空
    log.info(f"user_id={user_id}, ip_address={ip_address}, login_status={login_status}")
    if not ip_address or not login_status:
        raise BusinessException(
            code=400,
            message="用户ID、IP地址、登录状态不能为空"
        )

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

# async def service_logout(
#         db: AsyncSession,
#         username_or_email: str,
# ) -> None:
#     """
#     业务逻辑：
#     1. 根据用户名/邮箱查询用户
#     2. 记录登出信息
#     3.
#     失败则抛业务异常
#     """
#     # 调用 CRUD 层查询用户
#     try:
#         user: Optional[UserAccount] = await curd_user_account.get_by_username_or_email(
#             db=db, username_or_email=username_or_email
#         )

async def get_current_user(
        db: AsyncSession,
        username_or_email: str,
) -> UserAccount:
    """
    业务逻辑：
    1. 根据用户名/邮箱查询用户
    2. 校验用户是否存在
    3. 校验用户状态是否为 normal
    失败则抛业务异常
    """
    # 调用 CRUD 层查询用户
    try:
        user: Optional[UserAccount] = await curd_user_account.get_by_username_or_email(
            db=db, username_or_email=username_or_email
        )
    except SQLAlchemyError:
        raise exceptions.DatabaseOperationFailedException("query user")

    # 业务校验 1：用户是否存在
    if not user:
        raise exceptions.UserNotFoundException()

    # 业务校验 2：用户状态是否正常
    if user.status != "normal":
        raise exceptions.UserStatusForbiddenException(status=user.status)

    return user