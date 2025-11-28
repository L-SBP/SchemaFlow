# backend/app/api/v1/endpoints/user.py

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

# 隐式绝对导入
from api.v1.deps import get_db, get_current_active_user # 导入数据库和认证依赖
from schema import user as schemas # 导入 User Schema (UserMe, UserUpdatePassword, etc.)
from service import user_service # 导入 Service 层
# 👇 修改点1：导入正确的异常类 (去掉 PermissionDeniedException，添加 PasswordInvalidException, CodeInvalidException)
from core.exceptions import ItemNotFoundException, ValidationException, PasswordInvalidException, CodeInvalidException, UserAlreadyExistsException

router = APIRouter()

# ----------------------------------------------------------------------
# 1. GET /me - 获取当前用户信息
# ----------------------------------------------------------------------
@router.get("/me", response_model=schemas.UserMe)
async def read_user_me(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """
    获取当前用户详细信息 (对应前端 UserMe 响应)
    """
    try:
        user_dto = await user_service.get_user_me_service(db, current_user.user_id)
        return user_dto
    except ItemNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch user info: {e}")


# ----------------------------------------------------------------------
# 2. POST /password - 修改密码 (对应前端 6.1)
# ----------------------------------------------------------------------
@router.post("/password", response_model=schemas.UserMe)
async def update_password_endpoint(
    password_data: schemas.UserUpdatePassword,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """
    修改密码
    """
    try:
        updated_user_dto = await user_service.update_password_service(
            db,
            current_user.user_id,
            password_data
        )
        return updated_user_dto
    # 👇 修改点2：捕获 PasswordInvalidException (旧密码错误)
    except PasswordInvalidException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Password update failed: {e}")


# ----------------------------------------------------------------------
# 3. POST /username - 更新用户名
# ----------------------------------------------------------------------
@router.post("/username", response_model=schemas.UserMe)
async def update_username_endpoint(
    username_data: schemas.UserUpdateUsername,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """
    更新用户名
    """
    try:
        updated_user_dto = await user_service.update_username_service(
            db,
            current_user.user_id,
            username_data
        )
        return updated_user_dto
    # 👇 修改点3：捕获用户名已存在的异常
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Username update failed: {e}")


# ----------------------------------------------------------------------
# 4. POST /avatar - 更新头像
# ----------------------------------------------------------------------
@router.post("/avatar", response_model=schemas.UserMe)
async def update_avatar_endpoint(
    avatar_data: schemas.UserUpdateAvatar,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """
    更新头像
    """
    try:
        updated_user_dto = await user_service.update_avatar_service(
            db,
            current_user.user_id,
            avatar_data
        )
        return updated_user_dto
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Avatar update failed: {e}")


# ----------------------------------------------------------------------
# 5. POST /email/code - 请求更新邮箱 (对应前端 6.2)
# ----------------------------------------------------------------------
@router.post("/email/code", status_code=status.HTTP_204_NO_CONTENT)
async def request_update_email_endpoint(
    request_data: schemas.UserUpdateEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """
    请求更新邮箱 (发送验证码)
    """
    try:
        await user_service.request_update_email_service(db, current_user.user_id, request_data)
        return
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email update request failed: {e}")


# ----------------------------------------------------------------------
# 6. POST /email/confirm - 更新邮箱确认 (对应前端 6.3)
# ----------------------------------------------------------------------
@router.post("/email/confirm", response_model=schemas.UserMe)
async def confirm_update_email_endpoint(
    confirm_data: schemas.UserUpdateEmailConfirm,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """
    确认更新邮箱 (验证验证码)
    """
    try:
        updated_user_dto = await user_service.confirm_update_email_service(
            db,
            current_user.user_id,
            confirm_data
        )
        return updated_user_dto
    # 👇 修改点4：捕获 CodeInvalidException (验证码错误)
    except CodeInvalidException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Email confirmation failed: {e}")