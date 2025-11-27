from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from schema.unified_response import NoContentResponse, UnifiedSuccessResponse, LoginData
from schema.auth import UserSendCode, UserRegister, UserLogin

from api.v1.deps import get_db
from core import exceptions
from service import email_service
from service.user_service import service_register_user, service_login, create_login_record, \
    check_email_exists, service_save_token_in_redis, service_logout
from core.auth import create_access_token, oauth2_scheme

from core.log import log

auth_router = APIRouter()

@auth_router.post("/register/send-code", response_model=NoContentResponse)
async def send_register_code(
    payload: UserSendCode,
    db: AsyncSession = Depends(get_db)
):
    """
    路由层接收发注册码请求
    :param payload: 请求载荷，包含邮箱地址
    :param db: 数据库会话
    :return: 空响应
    """
    try:
        log.info("send register code")
        existing_user = await check_email_exists(db, payload.email)
        if existing_user:
            exc = exceptions.EmailHasBeenRegisteredException()
            raise HTTPException(
                status_code=exc.code,
                detail=[
                    {
                        "msg": exc.message
                    }
                ]
            )
        await email_service.service_send_verification_code(payload.email)
        log.info("send register code success")
        return NoContentResponse()
    except exceptions.BusinessException as e:
        log.error(f"Failed to send verification code: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=e.code,
            detail=[
                {
                    "msg": e.message
                }
            ]
        )
    except exceptions.AppException as e:
        log.error(f"Failed to send verification code: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=e.code,
            detail=[
                {
                    "msg": e.message
                }
            ]
        )


@auth_router.post("/register", response_model=UnifiedSuccessResponse[dict])
async def register(
    payload: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册接口
    :param payload: 注册请求载荷，包含用户名、邮箱、密码和验证码
    :param db: 数据库会话
    :return: 注册成功的用户信息
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
        # Convert to schema model for response
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
        raise HTTPException(
            status_code=e.code,
            detail=[
                {
                    "msg": e.message
                }
            ]
        )
    except exceptions.AppException as e:
        log.error(f"注册失败：{str(e)}", exc_info=True)  # exc_info=True 强制打印堆栈
        raise HTTPException(
            status_code=e.code,
            detail=[
                {
                    "msg": e.message
                }
            ]
        )


@auth_router.post("/login", response_model=UnifiedSuccessResponse[LoginData])
async def login(
        request: Request,
        payload: UserLogin,
        db: AsyncSession = Depends(get_db)
):
    """
    用户登录接口：验证用户+生成Token+存储登录记录（成功/失败都记录）
    :param request: HTTP请求对象，用于获取客户端信息
    :param payload: 登录请求载荷，包含用户名和密码
    :param db: 数据库会话
    :return: 包含访问令牌和用户信息的响应
    """
    # 初始化变量：存储登录记录需要的信息
    client_ip = request.client.host
    user_agent = request.headers.get("User-Agent", "")
    device_info = request.headers.get("X-Device-Info", "")
    log.info(f"Login request: client_ip={client_ip}, user_agent={user_agent}, device_infp={device_info}")

    try:
        exist_user = await service_login(db, payload.username, payload.password)

        log.info(f"start to record the login log")
        # 登录成功：存储成功登录记录
        await create_login_record(
            db=db,
            user_id=exist_user.user_id,
            ip_address=client_ip,
            login_status="success",
            user_agent=user_agent,
            device_info=device_info,
        )
        # 生成Token
        access_token=create_access_token(data={"sub": f"{exist_user.user_id}"})
        if not await service_save_token_in_redis(access_token):
            log.error("Failed to save token in redis")
            exc = exceptions.RedisOperationFailedException()
            raise HTTPException(
                status_code=exc.code,
                detail=[
                    {
                        "msg": exc.message
                    }
                ]
            )

        # 返回结果
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
    except exceptions.PasswordMismatchException as e:
        # 密码错误
        await create_login_record(
            db=db,
            user_id=exist_user.user_id,
            ip_address=client_ip,
            login_status="failed",
            failure_reason="密码错误",  # 失败原因（贴合表的failure_reason字段）
            user_agent=user_agent,
            device_info=device_info
        )
        # 抛出HTTP异常
        raise HTTPException(
            status_code=e.code,
            detail=[
                {
                    "msg": e.message
                }
            ]
        )
    except exceptions.UserStatusForbiddenException as e:
        # 状态异常
        await create_login_record(
            db=db,
            user_id=exist_user.user_id,
            ip_address=client_ip,
            login_status="failed",
            failure_reason=e.message,  # 失败原因（贴合表的failure_reason字段）
            user_agent=user_agent,
            device_info=device_info
        )
        # 抛出HTTP异常
        raise HTTPException(
            status_code=e.code,
            detail=[
                {
                    "msg": e.message
                }
            ]
        )
    except exceptions.BusinessException as e:
        # 业务异常
        await create_login_record(
            db=db,
            user_id=None,  # 无合法用户时设为None以避免外键约束冲突
            ip_address=client_ip,
            login_status="failed",
            failure_reason=e.message,  # 失败原因（贴合表的failure_reason字段）
            user_agent=user_agent,
            device_info=device_info
        )
        # 重新抛出HTTP异常
        raise HTTPException(
            status_code=e.code,
            detail=[
                {
                    "msg": e.message
                }
            ]
        ) from e

    except exceptions.AppException as e:
        # 系统异常
        await create_login_record(
            db=db,
            user_id=None,
            ip_address=client_ip,
            login_status="failed",
            failure_reason="系统内部错误",
            user_agent=user_agent,
            device_info=device_info
        )
        # 重新抛出500异常
        log.error(f"系统内部错误：{str(e)}", exc_info=True)
        raise HTTPException(
            status_code=e.code,
            detail=[
                {
                    "msg": e.message
                }
            ]
        ) from e

@auth_router.post("/logout", response_model=NoContentResponse)
async def logout(
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme)
):
    """
    路由层接收登出请求, 废除Token并记录登出
    :param db: 数据库会话
    :param token: JWT访问令牌
    :return: 空响应
    """
    try:
        result = await service_logout(db, token)
        if not result:
            exc = exceptions.RedisOperationFailedException()
            raise HTTPException(
                status_code=exc.code,
                detail=[
                    {
                        "msg": exc.message
                    }
                ]
            )

        return NoContentResponse()

    except exceptions.AppException as e:
        log.error(f"Logout failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=e.code,
            detail=[
                {
                    "msg": e.message
                }
            ]
        ) from e
    except Exception as e:
        log.error(f"Unexpected error during logout: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[
                {
                        "msg": "系统内部错误"
                }
            ]
        ) from e