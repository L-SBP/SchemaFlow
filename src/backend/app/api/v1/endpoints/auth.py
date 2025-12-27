"""
认证 API 端点。

处理用户注册、登录（包括 Swagger UI）、Token 刷新、登出及验证码发送。
"""
# backend/app/api/v1/endpoints/auth.py

from fastapi import APIRouter, Depends, status, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from schema.unified_response import UnifiedResponse, LoginData
from schema.auth import UserSendCode, UserRegister, UserLogin, ForgotPasswordRequest, ResetPasswordRequest
from fastapi.security import OAuth2PasswordRequestForm
from schema.token import Token # 记得导入这个
from api.v1.deps import get_db
from core import exceptions
from service import email_service
from service.user_service import service_register_user, service_login, create_login_record, \
    check_email_exists, service_save_token_in_redis, service_logout,service_check_user_exists,service_save_token_in_redis
from service.password_reset_service import service_send_password_reset_code, service_reset_password_with_code
from core.auth import create_access_token
# ：从 core.deps 导入 oauth2_scheme
from core.deps import get_db, oauth2_scheme
from core.log import log

# ：将 auth_router 改为 router，保持与其他模块一致
router = APIRouter()

# ============================================================
# 给 Swagger UI Authorize 按钮使用的登录接口
# ============================================================
@router.post("/swagger_login", response_model=Token)
async def swagger_login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    专门兼容 OAuth2 表单格式的登录接口。

    Args:
        db (AsyncSession): 数据库会话。
        form_data (OAuth2PasswordRequestForm): OAuth2 表单数据。

    Returns:
        Token: 访问令牌。

    Raises:
        HTTPException: 用户名密码错误(400)或 Token 保存失败(500)。
    """
    # 1. 验证用户
    user = await service_login(db, form_data.username, form_data.password)
    if not user:
        from core.exceptions import UserNotFoundException
        raise UserNotFoundException()
    
    if user.status != 'normal':
        from core.exceptions import UserStatusForbiddenException
        raise UserStatusForbiddenException(status=user.status, user_id=user.user_id)

    # 2. 生成 Token
    access_token = create_access_token(data={"sub": str(user.user_id)})
    
    # 3. 将 Token 存入 Redis 白名单
    # 如果不存，api/v1/deps.py 会因为查不到记录而报 Token revoked
    if not await service_save_token_in_redis(access_token):
        raise exceptions.RedisOperationFailedException()
    
    # 4. 返回 Token
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ：所有的装饰器 @auth_router.xxx 都改为 @router.xxx
@router.post("/register/send-code", response_model=UnifiedResponse[None])
async def send_register_code(
    payload: UserSendCode,
    db: AsyncSession = Depends(get_db)
):
    """
    发送注册验证码。

    Args:
        payload (UserSendCode): 请求载荷，包含邮箱地址。
        db (AsyncSession): 数据库会话。

    Returns:
        UnifiedResponse: 发送成功响应。

    Raises:
        HTTPException: 邮箱已注册或发送失败。
    """
    log.info("send register code")
    existing_user = await check_email_exists(db, payload.email)
    if existing_user:
        raise exceptions.EmailHasBeenRegisteredException()
    await email_service.service_send_verification_code(payload.email)
    log.info("send register code success")
    return UnifiedResponse.success(message="验证码发送成功")


@router.post("/register", response_model=UnifiedResponse[dict])
async def register(
    payload: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册接口。

    Args:
        payload (UserRegister): 注册请求载荷。
        db (AsyncSession): 数据库会话。

    Returns:
        UnifiedResponse: 注册成功的用户信息。

    Raises:
        HTTPException: 注册失败。
    """
    new_user = await service_register_user(
        db,
        username=payload.username,
        email=payload.email,
        password=payload.password,
        code=payload.verification_code
    )

    log.info("Registered user {}", new_user.username)
    return UnifiedResponse.success(
        data={
            "user_id": new_user.user_id,
            "username": new_user.username,
            "email": new_user.email,
            "status": new_user.status,
            "created_at": new_user.created_at
        },
        message="用户注册成功"
    )


@router.post("/login", response_model=UnifiedResponse[LoginData])
async def login(
        request: Request,
        payload: UserLogin,
        db: AsyncSession = Depends(get_db)
):
    """
    用户登录接口。
    
    验证用户、生成Token并记录登录日志。

    Args:
        request (Request): HTTP请求对象。
        payload (UserLogin): 登录请求载荷。
        db (AsyncSession): 数据库会话。

    Returns:
        UnifiedResponse: 包含Token和用户信息的响应。
    """
    # 初始化变量：存储登录记录需要的信息
    client_ip = request.client.host
    user_agent = request.headers.get("User-Agent", "")
    device_info = request.headers.get("X-Device-Info", "")
    log.info("Login request: client_ip={}, user_agent={}, device_infp={}", client_ip, user_agent, device_info)

    exist_user = await service_login(db, payload.username, payload.password)

    log.info("start to record the login log")
    await create_login_record(
        db=db,
        user_id=exist_user.user_id,
        ip_address=client_ip,
        login_status="success",
        user_agent=user_agent,
        device_info=device_info,
    )

    access_token = create_access_token(data={"sub": f"{exist_user.user_id}"})
    if not await service_save_token_in_redis(access_token):
        log.error("无法在Redis中保存令牌")
        raise exceptions.RedisOperationFailedException()

    # 获取完整的用户信息
    from service import user_service
    user_info = await user_service.get_user_me_service(db, exist_user.user_id)

    return UnifiedResponse.success(
        data=LoginData(
            access_token=access_token,
            token_type="bearer",
            user=user_info.dict()
        ),
        message="用户登录成功"
    )

@router.post("/logout", response_model=UnifiedResponse[None])
async def logout(
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme)
):
    """
    用户登出接口。
    
    废除 Token 并记录登出日志。

    Args:
        db (AsyncSession): 数据库会话。
        token (str): JWT 访问令牌。

    Returns:
        UnifiedResponse: 登出成功响应。

    Raises:
        HTTPException: 登出失败。
    """
    result = await service_logout(db, token)
    if not result:
        raise exceptions.RedisOperationFailedException()

    return UnifiedResponse.success(message="用户登出成功")


@router.post("/forgot-password", response_model=UnifiedResponse[None])
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """忘记密码：请求发送重置邮件。

    为避免用户枚举，无论邮箱是否存在，对外均返回成功。
    """

    client_ip = request.client.host if request.client else None
    await service_send_password_reset_code(db, payload.email, client_ip=client_ip)
    return UnifiedResponse.success(message="重置邮件发送成功")


@router.post("/reset-password", response_model=UnifiedResponse[None])
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """重置密码：校验邮箱验证码并设置新密码。"""

    await service_reset_password_with_code(db, payload.email, payload.verification_code, payload.new_password)
    return UnifiedResponse.success(message="密码重置成功")