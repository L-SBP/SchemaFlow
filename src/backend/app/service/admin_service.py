# backend/app/service/admin_service.py

from typing import List, Optional, Literal, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime  # 确保导入 datetime

from core.log import log
from core.exceptions import ItemNotFoundException, ValidationException

# 导入 DTO 和 CRUD
# 确保导入了所有具体的 Schema 类
from schema.admin import (
    AdminUserListResponse,
    AdminUserListItem,
    AdminUpdateUserStatusRequest,
    AdminUpdateUserStatusResponse,  # 新增导入
    AdminUpdateUserQuotaRequest,
    AdminUpdateUserQuotaResponse,  # 新增导入
    AnnouncementCreateRequest,
    AnnouncementResponse,
    AnnouncementUpdateRequest,
    AdminListResponse,
    AdminListItem,
    ViolationLogListResponse,
    ViolationLogListItem,
    AdminStatsResponse
)
from crud.crud_user_account import curd_user_account
from crud.crud_announcement import curd_announcement
from crud.crud_admin_data import curd_admin_data


# ----------------------------------------------------------------------
# 4.1 用户管理 Service
# ----------------------------------------------------------------------

async def get_admin_user_list_service(db: AsyncSession, page: int, page_size: int, search: Optional[str],
                                      status: str) -> AdminUserListResponse:
    """Service: 获取用户列表 (4.1.1)"""
    items_data, total = await curd_admin_data.get_user_list_with_stats(db, page, page_size, search, status)
    items_dto = [AdminUserListItem(**data) for data in items_data]
    return AdminUserListResponse(total=total, page=page, page_size=page_size, items=items_dto)


# 在参数列表中添加 admin_user_id: int
async def update_user_status_service(db: AsyncSession, user_id: int,
                                     data: AdminUpdateUserStatusRequest,
                                     admin_user_id: int) -> AdminUpdateUserStatusResponse:
    """修改用户状态 (4.1.2)"""
    # 1. 先查询用户是否存在 (获取 ORM 对象)
    user_obj = await curd_user_account.get(db, user_id)

    if not user_obj:
        raise ItemNotFoundException(f"User with ID {user_id} not found.")

    # 2. 业务逻辑：调用 CRUD 修改，传入 db_obj=user_obj
    updated_user = await curd_user_account.update(db, db_obj=user_obj, status=data.status)

    # 3. 业务逻辑：记录到 user_ban_log (占位，可后续实现)
    # await create_ban_log(db, user_id, admin_user_id, reason=data.reason, ...)

    return AdminUpdateUserStatusResponse(
        user_id=updated_user.user_id,
        status=updated_user.status,
        updated_at=datetime.now()
    )


async def update_user_quota_service(db: AsyncSession, user_id: int,
                                    data: AdminUpdateUserQuotaRequest) -> AdminUpdateUserQuotaResponse:
    """调整用户资源额度 (4.1.3)"""
    # 1. 先获取对象
    user_obj = await curd_user_account.get(db, user_id)

    if not user_obj:
        raise ItemNotFoundException(f"User with ID {user_id} not found.")

    # 2. 传入对象进行更新
    updated_user = await curd_user_account.update(db, db_obj=user_obj, max_databases=data.max_databases)

    return AdminUpdateUserQuotaResponse(
        user_id=updated_user.user_id,
        max_databases=updated_user.max_databases,
        updated_at=datetime.now()
    )


# ----------------------------------------------------------------------
# 4.2 公告管理 Service
# ----------------------------------------------------------------------

async def create_announcement_service(db: AsyncSession, data: AnnouncementCreateRequest,
                                      admin_user_id: int) -> AnnouncementResponse:
    """创建新公告 (4.2.1)"""
    announcement_orm = await curd_announcement.create(db, created_by=admin_user_id, **data.model_dump())
    return AnnouncementResponse.model_validate(announcement_orm)


async def update_announcement_service(db: AsyncSession, announcement_id: int,
                                      data: AnnouncementUpdateRequest) -> AnnouncementResponse:
    """更新公告内容和状态 (4.2.2)"""
    update_data = data.model_dump(exclude_unset=True)
    announcement_orm = await curd_announcement.update(db, announcement_id=announcement_id, update_data=update_data)
    if not announcement_orm:
        raise ItemNotFoundException("Announcement not found.")
    return AnnouncementResponse.model_validate(announcement_orm)


async def delete_announcement_service(db: AsyncSession, announcement_id: int) -> None:
    """删除公告 (4.2.3)"""
    success = await curd_announcement.remove(db, announcement_id)
    if not success:
        raise ItemNotFoundException("Announcement not found.")


# ----------------------------------------------------------------------
# 4.3/4.4 系统状态 Service
# ----------------------------------------------------------------------

async def get_admin_list_service(db: AsyncSession, page: int, page_size: int) -> AdminListResponse:
    """获取管理员列表 (4.3.1)"""
    admin_orms, total = await curd_admin_data.get_admin_list(db, page, page_size)
    items_dto = [AdminListItem.model_validate(orm) for orm in admin_orms]
    return AdminListResponse(total=total, page=page, page_size=page_size, items=items_dto)


async def get_violation_logs_service(db: AsyncSession, page: int, page_size: int, risk_level: Optional[str],
                                     resolution_status: Optional[str]) -> ViolationLogListResponse:
    """获取违规记录列表 (4.4.2)"""
    logs_data, total = await curd_admin_data.get_violation_logs(db, page, page_size, risk_level, resolution_status)
    items_dto = [ViolationLogListItem(**data) for data in logs_data]
    return ViolationLogListResponse(total=total, page=page, page_size=page_size, items=items_dto)


async def get_admin_stats_service(db: AsyncSession) -> AdminStatsResponse:
    """获取系统统计看板数据 (4.4.1)"""
    stats_data = await curd_admin_data.get_system_stats(db)
    return AdminStatsResponse(**stats_data)