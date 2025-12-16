"""
管理员 API 端点。提供用户管理、公告管理、违规记录查看及系统统计看板等管理员专属功能。
"""
from typing import Optional, Literal, Any
from fastapi import APIRouter, Depends, Query, Path, status, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession as Session

# 导入 Service 和 Schema
from service import admin_service as service
from schema.admin import (
    AdminUserListResponse, AdminUpdateUserStatusRequest, AdminUpdateUserStatusResponse,
    AdminUpdateUserQuotaRequest, AdminUpdateUserQuotaResponse,
    AnnouncementCreateRequest, AnnouncementUpdateRequest, AnnouncementResponse,
    AdminListResponse, ViolationLogListResponse, AdminStatsResponse
)
from schema.user import UserMe
# 导入依赖
from api.v1.deps import get_db, get_current_admin_user
from core.exceptions import ItemNotFoundException

router = APIRouter()

# 统一管理员权限依赖
AdminDependency = Depends(get_current_admin_user)

# 统一分页参数 DTO
class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    ):
        self.page = page
        self.page_size = page_size

# ----------------------------------------------------------------------
# 4.1. 用户管理
# ----------------------------------------------------------------------
@router.get("/users", response_model=AdminUserListResponse, summary="4.1.1 获取用户列表")
async def get_user_list(
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="按用户名/邮箱搜索"),
    # 变量名改为 filter_status，增加 alias="status"
    filter_status: Literal["normal", "banned", "all"] = Query("all", alias="status", description="按状态筛选"),
) -> Any:
    """
    获取用户列表，支持搜索和筛选。

    Args:
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。
        pagination (PaginationParams): 分页参数。
        search (Optional[str]): 按用户名/邮箱搜索关键字。
        filter_status (Literal["normal", "banned", "all"]): 按状态筛选用户。

    Returns:
        AdminUserListResponse: 用户列表响应。

    Raises:
        HTTPException: 内部服务器错误(500)。
    """
    try:
        # 这里传入 filter_status
        return await service.get_admin_user_list_service(
            db, pagination.page, pagination.page_size, search, filter_status
        )
    except Exception as e:
        # 现在这里的 status 引用的是 fastapi.status 模块，不会报错了
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/users/{user_id}/status", response_model=AdminUpdateUserStatusResponse, summary="4.1.2 修改用户状态 (封禁/解封)")
async def update_user_status(
    # 修正：将 data 移到 user_id 之前
    data: AdminUpdateUserStatusRequest,
    user_id: int = Path(..., description="目标用户ID"),
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    封禁或解封用户。

    Args:
        data (AdminUpdateUserStatusRequest): 用户状态更新请求体。
        user_id (int): 目标用户ID。
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        AdminUpdateUserStatusResponse: 更新后的用户状态信息。

    Raises:
        HTTPException: 用户未找到(404)或内部服务器错误(500)。
    """
    try:
        return await service.update_user_status_service(db, user_id, data, admin_user.user_id)
    except ItemNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update user status: {e}")


@router.patch("/users/{user_id}/quota", response_model=AdminUpdateUserQuotaResponse, summary="4.1.3 调整用户资源额度")
async def update_user_quota(
    # 修正：将 data 移到 user_id 之前
    data: AdminUpdateUserQuotaRequest,
    user_id: int = Path(..., description="目标用户ID"),
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    调整用户的最大数据库额度。

    Args:
        data (AdminUpdateUserQuotaRequest): 用户额度更新请求体。
        user_id (int): 目标用户ID。
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        AdminUpdateUserQuotaResponse: 更新后的用户额度信息。

    Raises:
        HTTPException: 用户未找到(404)或内部服务器错误(500)。
    """
    try:
        return await service.update_user_quota_service(db, user_id, data)
    except ItemNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to adjust quota: {e}")

# ----------------------------------------------------------------------
# 4.2. 公告管理
# ----------------------------------------------------------------------

@router.post("/announcements", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED, summary="4.2.1 创建公告")
async def create_announcement(
    data: AnnouncementCreateRequest,
    db: Session = Depends(get_db),
    current_admin: UserMe = AdminDependency,
) -> Any:
    """
    创建新的系统公告。

    Args:
        data (AnnouncementCreateRequest): 公告创建请求体。
        db (Session): 数据库会话。
        current_admin (UserMe): 当前管理员用户。

    Returns:
        AnnouncementResponse: 创建后的公告信息。

    Raises:
        HTTPException: 内部服务器错误(500)。
    """
    try:
        return await service.create_announcement_service(db, data, current_admin.user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create announcement: {e}")


@router.put("/announcements/{announcement_id}", response_model=AnnouncementResponse, summary="4.2.2 更新公告")
async def update_announcement(
    # 修正：将 data 移到 announcement_id 之前
    data: AnnouncementUpdateRequest,
    announcement_id: int = Path(..., description="公告ID"),
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    更新公告内容和状态。

    Args:
        data (AnnouncementUpdateRequest): 公告更新请求体。
        announcement_id (int): 公告ID。
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        AnnouncementResponse: 更新后的公告信息。

    Raises:
        HTTPException: 公告未找到(404)或内部服务器错误(500)。
    """
    try:
        return await service.update_announcement_service(db, announcement_id, data)
    except ItemNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update announcement: {e}")


@router.delete("/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT, summary="4.2.3 删除公告")
async def delete_announcement(
    announcement_id: int = Path(..., description="公告ID"),
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> None:
    """
    删除指定的公告。

    Args:
        announcement_id (int): 公告ID。
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        None: 无返回内容。

    Raises:
        HTTPException: 公告未找到(404)或内部服务器错误(500)。
    """
    try:
        await service.delete_announcement_service(db, announcement_id)
        return
    except ItemNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete announcement: {e}")

# ----------------------------------------------------------------------
# 4.3. 管理员状态 / 4.4. 违规记录与统计
# ----------------------------------------------------------------------

@router.get("/admins", response_model=AdminListResponse, summary="4.3.1 获取管理员列表")
async def get_admin_list(
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
    pagination: PaginationParams = Depends(),
) -> Any:
    """
    获取所有管理员的列表。

    Args:
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。
        pagination (PaginationParams): 分页参数。

    Returns:
        AdminListResponse: 管理员列表响应。

    Raises:
        HTTPException: 内部服务器错误(500)。
    """
    try:
        return await service.get_admin_list_service(db, pagination.page, pagination.page_size)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch admin list: {e}")


@router.get("/violations", response_model=ViolationLogListResponse, summary="4.4.2 获取违规记录列表")
async def get_violation_logs(
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
    pagination: PaginationParams = Depends(),
    risk_level: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = Query(None, description="风险等级筛选"),
    resolution_status: Optional[Literal["pending", "in_progress", "resolved", "ignored"]] = Query(None, description="处理状态筛选"),
) -> Any:
    """
    获取用户违规操作记录列表，支持筛选。

    Args:
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。
        pagination (PaginationParams): 分页参数。
        risk_level (Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]]): 风险等级筛选。
        resolution_status (Optional[Literal["pending", "in_progress", "resolved", "ignored"]]): 处理状态筛选。

    Returns:
        ViolationLogListResponse: 违规记录列表响应。

    Raises:
        HTTPException: 内部服务器错误(500)。
    """
    try:
        return await service.get_violation_logs_service(
            db, pagination.page, pagination.page_size, risk_level, resolution_status
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch violations: {e}")


@router.get("/dashboard/stats", response_model=AdminStatsResponse, summary="4.4.1 获取系统统计看板")
async def get_system_stats(
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    获取系统运行的实时统计数据。

    Args:
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        AdminStatsResponse: 系统统计响应。

    Raises:
        HTTPException: 内部服务器错误(500)。
    """
    try:
        return await service.get_admin_stats_service(db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch stats: {e}")
