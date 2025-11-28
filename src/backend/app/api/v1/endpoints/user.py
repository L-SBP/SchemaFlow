# backend/app/api/v1/endpoints/user.py

from fastapi import APIRouter, Depends, HTTPException, status, Body, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

# 隐式绝对导入
from api.v1.deps import get_db, get_current_active_user
from schema import user as schemas # 导入 User Schema (UserMe, UserUpdatePassword, etc.)
from service import user_service # 导入 Service 层
# 导入所有必要的业务异常
from core.exceptions import ItemNotFoundException, ValidationException, PasswordInvalidException, CodeInvalidException, UserAlreadyExistsException, UserNotFoundException

router = APIRouter()

# ----------------------------------------------------------------------
# 1. GET /users/me - 获取当前用户信息 (Doc 3.1.1)
# ----------------------------------------------------------------------
@router.get("/me", response_model=schemas.UserMe)
async def read_user_me(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """
    获取当前登录用户详细信息。
    """
    try:
        # Service 层负责将 ORM 转换为 UserMe DTO
        user_dto = await user_service.get_user_me_service(db, current_user.user_id)
        return user_dto
    except ItemNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch user info: {e}")


# ----------------------------------------------------------------------
# 2. PATCH /users/me - 更新用户名 (Doc 3.1.2)
# ----------------------------------------------------------------------
@router.patch("/me", response_model=schemas.UserMe)
async def update_username_endpoint(
    username_data: schemas.UserUpdateUsername,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """
    更新当前用户名。
    """
    try:
        updated_user_dto = await user_service.update_username_service(
            db,
            current_user.user_id,
            username_data
        )
        # 成功返回 200 OK，返回更新后的 DTO
        return updated_user_dto
    # 捕获用户名已存在的异常
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Username update failed: {e}")


# ----------------------------------------------------------------------
# 3. PUT /users/me/password - 修改密码 (Doc 3.1.3)
# ----------------------------------------------------------------------
@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password_endpoint(
    password_data: schemas.UserUpdatePassword,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> None:
    """
    更新当前用户密码 (成功返回 204 No Content)。
    """
    try:
        await user_service.update_password_service(
            db,
            current_user.user_id,
            password_data
        )
        # 成功返回 None (204 No Content)
        return None
    # 捕获旧密码错误
    except PasswordInvalidException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Password update failed: {e}")


# ----------------------------------------------------------------------
# 4. POST /users/me/avatar - 上传/更换头像 (Doc 3.1.6)
# ----------------------------------------------------------------------
@router.post("/me/avatar", response_model=schemas.UserUpdateAvatar)
async def update_avatar_endpoint(
    # 修正：使用 File 和 UploadFile 处理 multipart/form-data
    file: UploadFile = File(..., description="头像文件 (JPG/PNG)", max_size=2000000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """
    上传新头像 (处理文件上传)。
    """
    try:
        # Service 负责文件存储和更新 avatar_url
        updated_avatar_dto = await user_service.update_avatar_service(
            db,
            current_user.user_id,
            file # 传递文件对象给 Service 层
        )
        return updated_avatar_dto # 成功返回 { "avatar_url": "..." } DTO
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Avatar upload failed: {e}")


# ----------------------------------------------------------------------
# 5. POST /users/me/email/send-code - 请求更新邮箱 (Doc 3.1.4)
# ----------------------------------------------------------------------
@router.post("/me/email/send-code", status_code=status.HTTP_204_NO_CONTENT)
async def request_update_email_endpoint(
    request_data: schemas.UserUpdateEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> None:
    """
    向新邮箱发送验证码 (成功返回 204 No Content)。
    """
    try:
        await user_service.request_update_email_service(db, current_user.user_id, request_data)
        return
    # 捕获邮箱已被注册的异常
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email update request failed: {e}")


# ----------------------------------------------------------------------
# 6. PUT /users/me/email - 更新邮箱确认 (Doc 3.1.5)
# ----------------------------------------------------------------------
@router.put("/me/email", response_model=schemas.UserMe)
async def confirm_update_email_endpoint(
    confirm_data: schemas.UserUpdateEmailConfirm,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """
    确认邮箱变更 (验证验证码) (成功返回 200 OK)。
    """
    try:
        updated_user_dto = await user_service.confirm_update_email_service(
            db,
            current_user.user_id,
            confirm_data
        )
        return updated_user_dto
    # 捕获验证码错误
    except CodeInvalidException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Email confirmation failed: {e}")