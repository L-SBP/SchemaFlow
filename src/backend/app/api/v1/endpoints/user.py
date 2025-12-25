"""
用户 API 端点。

处理当前用户的个人信息查询、修改（用户名、密码、头像、邮箱）及登录历史查询。
"""

# backend/app/api/v1/endpoints/user.py

from fastapi import APIRouter, Depends, status, Body, File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from .. import deps
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

    Args:
        db (AsyncSession): 数据库会话。
        current_user (User): 当前登录用户。

    Returns:
        UserMe: 用户信息。

    Raises:
        HTTPException: 用户未找到(404)或内部服务器错误(500)。
    """
    # Service 层负责将 ORM 转换为 UserMe DTO
    return await user_service.get_user_me_service(db, current_user.user_id)


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

    Args:
        username_data (schemas.UserUpdateUsername): 用户名更新请求体。
        db (AsyncSession): 数据库会话。
        current_user (User): 当前登录用户。

    Returns:
        UserMe: 更新后的用户信息。

    Raises:
        HTTPException: 用户名已存在(409)、验证失败(422)或内部服务器错误(500)。
    """
    updated_user_dto = await user_service.update_username_service(
        db,
        current_user.user_id,
        username_data
    )
    # 成功返回 200 OK，返回更新后的 DTO
    return updated_user_dto


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

    Args:
        password_data (schemas.UserUpdatePassword): 密码更新请求体。
        db (AsyncSession): 数据库会话。
        current_user (User): 当前登录用户。

    Returns:
        None

    Raises:
        HTTPException: 密码错误(401)或内部服务器错误(500)。
    """
    await user_service.update_password_service(
        db,
        current_user.user_id,
        password_data
    )
    # 成功返回 None (204 No Content)
    return None


# ----------------------------------------------------------------------
# 4. POST /users/me/avatar - 上传/更换头像 (Doc 3.1.6)
# ----------------------------------------------------------------------
@router.post("/me/avatar", response_model=schemas.UserUpdateAvatar)
async def update_avatar_endpoint(
    # 错误代码 (当前): file: UploadFile = File(...)
    # 修正代码: 改回接收 JSON Body
    avatar_data: schemas.UserUpdateAvatar,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """
    更新头像 URL (接收 JSON)。

    Args:
        avatar_data (schemas.UserUpdateAvatar): 头像更新请求体。
        db (AsyncSession): 数据库会话。
        current_user (User): 当前登录用户。

    Returns:
        UserUpdateAvatar: 更新后的头像信息。

    Raises:
        HTTPException: 内部服务器错误(500)。
    """
    # Service 期望接收的是 schemas.UserUpdateAvatar 对象
    updated_avatar_dto = await user_service.update_avatar_service(
        db,
        current_user.user_id,
        avatar_data  # 传递 Pydantic Schema
    )
    return updated_avatar_dto

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

    Args:
        request_data (schemas.UserUpdateEmailRequest): 邮箱更新请求体。
        db (AsyncSession): 数据库会话。
        current_user (User): 当前登录用户。

    Returns:
        None
    """
    await user_service.request_update_email_service(db, current_user.user_id, request_data)
    return


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

    Args:
        confirm_data (schemas.UserUpdateEmailConfirm): 邮箱更新确认请求体。
        db (AsyncSession): 数据库会话。
        current_user (User): 当前登录用户。

    Returns:
        UserMe: 更新后的用户信息。
    """
    updated_user_dto = await user_service.confirm_update_email_service(
        db,
        current_user.user_id,
        confirm_data
    )
    return updated_user_dto


@router.get("/me/login-history", response_model=schemas.PaginatedLoginHistory)
async def read_login_history(
        db: AsyncSession = Depends(deps.get_db),
        current_user=Depends(deps.get_current_active_user),
        # 接收标准分页参数
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页数量"),  # Doc 要求默认 10
) -> Any:
    """
    获取当前用户的登录历史记录 (包含分页)。

    Args:
        db (AsyncSession): 数据库会话。
        current_user (User): 当前登录用户。
        page (int): 页码。
        page_size (int): 每页数量。

    Returns:
        PaginatedLoginHistory: 分页登录历史记录。
    """
    # Router 严格只调用 Service
    history_list = await user_service.get_login_history_service(
        db,
        user_id=current_user.user_id,
        page=page,
        page_size=page_size
    )
    return history_list
