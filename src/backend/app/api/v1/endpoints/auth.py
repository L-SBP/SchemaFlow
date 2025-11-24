from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from schema.unified_response import NoContentResponse, UnifiedSuccessResponse, ErrorResponse, LoginData
from schema.auth import UserSendCode, UserRegister, UserLogin

from api.v1.deps import get_db
from models import user_account as user_account_model, user_login_history
from core import exceptions
from service import email_service
from service.user_service import service_register_user, service_login, create_login_record, \
    check_email_exists, get_current_user
from core.auth import create_access_token

from core.log import log

auth_router = APIRouter()

@auth_router.post("/register/send-code", response_model=NoContentResponse)
async def send_register_code(
    payload: UserSendCode,
    db: AsyncSession = Depends(get_db)
):
    """
    路由层接收发注册码请求
    :param payload:
    :param db:
    :return:
    """
    log.info("send register code")
    existing_user = await check_email_exists(db, payload.email)
    if existing_user:
        raise exceptions.EmailHasBeenRegisteredException()
    await email_service.service_send_verification_code(payload.email)
    return NoContentResponse()


@auth_router.post("/register", response_model=UnifiedSuccessResponse[dict])
async def register(
    payload: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    注册接口：
    :param payload:
    :param db:
    :return:
    """
    try:
        log.info("register")
        log.info(f"Payload 正常：username={payload.username}, email={payload.email}, code={payload.verification_code}")
        log.info(f"service_register_user 函数是否存在：{service_register_user is not None}")
        log.info(f"db 会话是否有效：{db is not None}")

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
            detail=e.message
        )
    except Exception as e:
        # 重点：打印完整异常堆栈（包括导入错误、NameError 等）
        log.error(f"注册失败：{str(e)}", exc_info=True)  # exc_info=True 强制打印堆栈
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"内部错误：{str(e)}"
             )


@auth_router.post("/login", response_model=UnifiedSuccessResponse[LoginData])
async def login(
        request: Request,
        payload: UserLogin,
        db: AsyncSession = Depends(get_db)
):
    """
    登录接口：验证用户+生成Token+存储登录记录（成功/失败都记录）
    :param request:
    :param payload:
    :param db:
    :return:
    """
    # 初始化变量：存储登录记录需要的信息
    client_ip = request.client.host
    user_agent = request.headers.get("User-Agent", "")
    device_info = request.headers.get("X-Device-Info", "")
    log.info(f"Login request: client_ip={client_ip}, user_agent={user_agent}, device_infp={device_info}")

    try:
        # 1. 调用Service层验证用户
        user = await service_login(
            username_or_email=payload.username,
            password=payload.password,
            db=db
        )

        log.info(f"start to record the login log")
        # 2. 登录成功：存储成功登录记录
        await create_login_record(
            db=db,
            user_id=user.user_id,
            ip_address=client_ip,
            login_status="success",
            user_agent=user_agent,
            device_info=device_info,
        )

        # 3. 生成Token+返回结果
        return UnifiedSuccessResponse.create(
            data=LoginData(
                access_token=create_access_token(data={"sub": user.username}),
                token_type="bearer",
                user={
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "is_admin": user.is_admin,
                    "avatar_url": user.avatar_url
                }
            ),
            message="用户登录成功"
        )

    except exceptions.BusinessException as e:
        # 4. 业务异常（如用户名密码错误、用户未激活）：存储「失败登录记录」
        await create_login_record(
            db=db,
            user_id=0,  # 无合法用户时设为0（或根据业务逻辑调整，如查询不到用户时为0）
            ip_address=client_ip,
            login_status="failed",
            failure_reason=e.message,  # 失败原因（贴合表的failure_reason字段）
            user_agent=user_agent,
            device_info=device_info
        )
        # 重新抛出HTTP异常
        raise HTTPException(
            status_code=e.code,
            detail=e.message
        ) from e

    except Exception as e:
        # 5. 系统异常（如数据库错误）：存储「失败登录记录」
        await create_login_record(
            db=db,
            user_id=0,
            ip_address=client_ip,
            login_status="failed",
            failure_reason="系统内部错误",
            user_agent=user_agent,
            device_info=device_info
        )
        # 重新抛出500异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) from e

# @router.post("/logout", response_model=NoContentResponse)
# async def logout(
#         db: AsyncSession = Depends(get_db),
#         current_user: user_account_model.UserAccount = Depends(get_current_user)
# ):
#     """
#     路由层接收登出请求, 废除Token并记录登出
#     :param db:
#     :param current_user:
#     :return:
#     """
#     from sqlalchemy import select
#     query = select(user_login_history.UserLoginHistory).where(
#         user_login_history.UserLoginHistory.user_id == current_user.user_id,
#         user_login_history.UserLoginHistory.login_status == "success"
#     ).order_by(user_login_history.UserLoginHistory.login_time.desc()).limit(1)
#
#     result = await db.execute(query)
#     entry = result.scalars().first()
#
#     if entry and not entry.logout_time:
#         entry.logout_time = datetime.now(timezone.utc)
#         entry.session_duration = entry.logout_time - entry.login_time
#         entry.login_status = "forced_logout"
#         await db.commit()
#     return