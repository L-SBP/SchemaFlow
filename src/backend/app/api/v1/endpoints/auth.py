"""
认证 API 端点。

处理用户注册、登录（包括 Swagger UI）、Token 刷新、登出及验证码发送。
"""
# backend/app/api/v1/endpoints/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from schema.unified_response import NoContentResponse, UnifiedSuccessResponse, LoginData
from schema.auth import UserSendCode, UserRegister, UserLogin
from fastapi.security import OAuth2PasswordRequestForm
from schema.token import Token # 记得导入这个
from api.v1.deps import get_db
from core import exceptions
from service import email_service
from service.user_service import service_register_user, service_login, create_login_record, \
    check_email_exists, service_save_token_in_redis, service_logout,service_check_user_exists,service_save_token_in_redis
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
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    if user.status != 'normal':
         raise HTTPException(status_code=400, detail="User is inactive")

    # 2. 生成 Token
    access_token = create_access_token(data={"sub": str(user.user_id)})
    
    # 3. 将 Token 存入 Redis 白名单
    # 如果不存，api/v1/deps.py 会因为查不到记录而报 Token revoked
    if not await service_save_token_in_redis(access_token):
        raise HTTPException(status_code=500, detail="Failed to save token session")
    
    # 4. 返回 Token
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ：所有的装饰器 @auth_router.xxx 都改为 @router.xxx
@router.post("/register/send-code", response_model=NoContentResponse)
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
        NoContentResponse: 空响应。

    Raises:
        HTTPException: 邮箱已注册或发送失败。
    """
    try:
        log.info("send register code")
        existing_user = await check_email_exists(db, payload.email)
        if existing_user:
            exc = exceptions.EmailHasBeenRegisteredException()
            # 直接传入字符串 message
            raise HTTPException(
                status_code=exc.code,
                detail=exc.message
            )
        await email_service.service_send_verification_code(payload.email)
        log.info("send register code success")
        return NoContentResponse()
    except exceptions.BusinessException as e:
        log.error(f"Failed to send verification code: {str(e)}", exc_info=True)
        # 直接传入字符串 message
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )
    except exceptions.AppException as e:
        log.error(f"Failed to send verification code: {str(e)}", exc_info=True)
        # 直接传入字符串 message
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )


@router.post("/register", response_model=UnifiedSuccessResponse[dict])
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
        UnifiedSuccessResponse: 注册成功的用户信息。

    Raises:
        HTTPException: 注册失败。
    """
    try:
        new_user = await service_register_user(
            db,
            username=payload.username,
            email=payload.email,
            password=payload.password,
            code=payload.verification_code
        )

        log.info(f"Registered user {new_user.username}")
        return UnifiedSuccessResponse.create(
            data={
                "user_id": new_user.user_id,
                "username": new_user.username,
                "email": new_user.email,
                "status": new_user.status,
                "created_at": new_user.created_at
            },
            message="用户注册成功"
        )
    except exceptions.BusinessException as e:
        #  直接传入字符串 message
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )
    except exceptions.AppException as e:
        log.error(f"注册失败：{str(e)}", exc_info=True)
        #  直接传入字符串 message
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )


@router.post("/login", response_model=UnifiedSuccessResponse[LoginData])
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
        UnifiedSuccessResponse: 包含Token和用户信息的响应。

    Raises:
        HTTPException: 登录失败。
    """
    # 初始化变量：存储登录记录需要的信息
    client_ip = request.client.host
    user_agent = request.headers.get("User-Agent", "")
    device_info = request.headers.get("X-Device-Info", "")
    log.info(f"Login request: client_ip={client_ip}, user_agent={user_agent}, device_infp={device_info}")

    try:
        exist_user = await service_login(db, payload.username, payload.password)

        log.info(f"start to record the login log")
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
            log.error("Failed to save token in redis")
            exc = exceptions.RedisOperationFailedException()
            #  直接传入字符串 message
            raise HTTPException(
                status_code=exc.code,
                detail=exc.message
            )

        return UnifiedSuccessResponse.create(
            data=LoginData(
                access_token=access_token,
                token_type="bearer",
                user={
                    "user_id": exist_user.user_id,
                    "username": exist_user.username,
                    "email": exist_user.email,
                    "is_admin": exist_user.is_admin,
                    "avatar_url": exist_user.avatar_url
                }
            ),
            message="用户登录成功"
        )
    except exceptions.PasswordInvalidException as e:
        # ：手动查用户ID用于记日志
        current_user = await service_check_user_exists(db, payload.username)
        user_id = current_user.user_id if current_user else None

        await create_login_record(
            db=db,
            user_id=user_id,
            ip_address=client_ip,
            login_status="failed",
            failure_reason="密码错误",
            user_agent=user_agent,
            device_info=device_info
        )
        #  直接传入字符串 message
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )
    except exceptions.UserStatusForbiddenException as e:
        # ：手动查用户ID用于记日志
        current_user = await service_check_user_exists(db, payload.username)
        user_id = current_user.user_id if current_user else None

        await create_login_record(
            db=db,
            user_id=user_id,
            ip_address=client_ip,
            login_status="failed",
            failure_reason=e.message,
            user_agent=user_agent,
            device_info=device_info
        )
        #  直接传入字符串 message
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        )
    except exceptions.BusinessException as e:
        await create_login_record(
            db=db,
            user_id=None,
            ip_address=client_ip,
            login_status="failed",
            failure_reason=e.message,
            user_agent=user_agent,
            device_info=device_info
        )
        # 直接传入字符串 message
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        ) from e

    except exceptions.AppException as e:
        await create_login_record(
            db=db,
            user_id=None,
            ip_address=client_ip,
            login_status="failed",
            failure_reason="系统内部错误",
            user_agent=user_agent,
            device_info=device_info
        )
        log.error(f"系统内部错误：{str(e)}", exc_info=True)
        # 直接传入字符串 message
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        ) from e

@router.post("/logout", response_model=NoContentResponse)
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
        NoContentResponse: 空响应。

    Raises:
        HTTPException: 登出失败。
    """
    try:
        result = await service_logout(db, token)
        if not result:
            exc = exceptions.RedisOperationFailedException()
            #  直接传入字符串 message
            raise HTTPException(
                status_code=exc.code,
                detail=exc.message
            )

        return NoContentResponse()

    except exceptions.AppException as e:
        log.error(f"Logout failed: {str(e)}", exc_info=True)
        # 直接传入字符串 message
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        ) from e
    except Exception as e:
        log.error(f"Unexpected error during logout: {str(e)}", exc_info=True)
        # 直接传入字符串 message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="系统内部错误"
        ) from e