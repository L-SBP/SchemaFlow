"""
管理员服务。

提供用户、公告与系统统计的管理能力，进行输入校验、调用 CRUD 层，并整形为
管理端响应。
"""

# backend/app/service/admin_service.py

from typing import List, Optional, Literal, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta  # 确保导入 datetime
from sqlalchemy import select, desc, and_

from core.log import log
from core.exceptions import ItemNotFoundException, ValidationException

# 导入 DTO 和 CRUD
# 确保导入了所有具体的 Schema 类
from schema.admin import (
    AdminUserListResponse,
    AdminUserListItem,
    AdminUpdateUserStatusRequest,
    AdminUpdateUserStatusResponse,
    AdminUpdateUserQuotaRequest,
    AdminUpdateUserQuotaResponse,
    AnnouncementCreateRequest,
    AnnouncementResponse,
    AnnouncementUpdateRequest,
    AdminListResponse,
    AdminListItem,
    ViolationLogListResponse,
    ViolationLogListItem,
    AdminStatsResponse,
    AdminUserDetailResponse,
    AdminUserProjectItem,
    AdminUserLoginHistoryItem
)
from crud.crud_user_account import crud_user_account
from crud.crud_announcement import crud_announcement
from crud.crud_admin_data import crud_admin_data
from crud.crud_project import crud_project
from crud.crud_user_login_history import crud_login_history


# ----------------------------------------------------------------------
# 用户管理
# ----------------------------------------------------------------------

async def get_admin_user_list_service(
    db: AsyncSession,
    page: int,
    page_size: int,
    search: Optional[str],
    status: str,
) -> AdminUserListResponse:
    """
    获取管理员视角的用户列表。

    Args:
        db (AsyncSession): 数据库会话。
        page (int): 页码。
        page_size (int): 每页数量。
        search (Optional[str]): 搜索关键字。
        status (str): 用户状态过滤条件。

    Returns:
        AdminUserListResponse: 包含分页信息与用户条目的响应。
    """
    items_data, total = await crud_admin_data.get_user_list_with_stats(db, page, page_size, search, status)
    items_dto = [AdminUserListItem(**data) for data in items_data]
    return AdminUserListResponse(total=total, page=page, page_size=page_size, items=items_dto)


async def get_admin_user_detail_service(
    db: AsyncSession,
    user_id: int,
    project_limit: int = 100,
    login_limit: int = 20,
) -> AdminUserDetailResponse:
    """获取管理员视角的用户详情（额度、已创建项目、登录历史）。"""

    user_obj = await crud_user_account.get(db, user_id)
    if not user_obj:
        raise ItemNotFoundException(f"User with ID {user_id} not found.")

    project_limit = max(0, min(project_limit, 500))
    login_limit = max(0, min(login_limit, 200))

    project_count = await crud_project.get_total_count_by_user(db, user_id)
    projects = await crud_project.get_by_user(db, user_id, skip=0, limit=project_limit)

    login_history_items, _total_login = await crud_login_history.get_multi_by_user(
        db, user_id, skip=0, limit=login_limit
    )

    return AdminUserDetailResponse(
        user_id=user_obj.user_id,
        username=user_obj.username,
        email=user_obj.email,
        status=user_obj.status,
        max_databases=user_obj.max_databases,
        project_count=project_count,
        last_login_at=user_obj.last_login_at,
        created_at=getattr(user_obj, "created_at", None),
        avatar_url=user_obj.avatar_url,
        projects=[
            AdminUserProjectItem(
                project_id=p.project_id,
                project_name=p.project_name,
                db_type=getattr(p, "db_type", None),
                project_status=p.project_status,
                created_at=p.created_at,
                description=p.description,
            )
            for p in projects
        ],
        login_history=[
            AdminUserLoginHistoryItem(
                login_id=lh.login_id,
                login_time=lh.login_time,
                logout_time=lh.logout_time,
                ip_address=lh.ip_address,
                user_agent=lh.user_agent,
                login_status=lh.login_status,
                failure_reason=lh.failure_reason,
            )
            for lh in login_history_items
        ],
    )


# 在参数列表中添加 admin_user_id: int
async def update_user_status_service(
    db: AsyncSession,
    user_id: int,
    data: AdminUpdateUserStatusRequest,
    admin_user_id: int,
) -> AdminUpdateUserStatusResponse:
    """
    修改指定用户的状态。

    Args:
        db (AsyncSession): 数据库会话。
        user_id (int): 目标用户 ID。
        data (AdminUpdateUserStatusRequest): 状态更新请求体。
        admin_user_id (int): 执行操作的管理员用户 ID。

    Returns:
        AdminUpdateUserStatusResponse: 更新后的状态信息。

    Raises:
        ItemNotFoundException: 用户不存在。
    """
    # 1. 先查询用户是否存在 (获取 ORM 对象)
    user_obj = await crud_user_account.get(db, user_id)

    if not user_obj:
        raise ItemNotFoundException(f"User with ID {user_id} not found.")

    # 2. 业务逻辑：调用 CRUD 修改，传入 db_obj=user_obj
    updated_user = await crud_user_account.update(db, db_obj=user_obj, status=data.status)

    # 3. 如果用户被解封（状态变为normal），重置登录失败计数和请求频率
    if data.status == 'normal':
        from core.security import login_failure_tracker, freq_limiter
        await login_failure_tracker.reset_failed_count(user_id)
        freq_limiter.reset_frequency(user_id)
        log.info(f"管理员 {admin_user_id} 修改用户 {user_id} 状态为 normal，已重置登录失败计数和请求频率")

    # 4. 业务逻辑：记录到 user_ban_log (占位，可后续实现)
    # await create_ban_log(db, user_id, admin_user_id, reason=data.reason, ...)

    return AdminUpdateUserStatusResponse(
        user_id=updated_user.user_id,
        status=updated_user.status,
        updated_at=datetime.now()
    )


async def update_user_quota_service(
    db: AsyncSession,
    user_id: int,
    data: AdminUpdateUserQuotaRequest
) -> AdminUpdateUserQuotaResponse:
    """
    调整用户的资源额度。

    Args:
        db (AsyncSession): 数据库会话。
        user_id (int): 目标用户 ID。
        data (AdminUpdateUserQuotaRequest): 额度更新请求体。

    Returns:
        AdminUpdateUserQuotaResponse: 更新后的额度信息。

    Raises:
        ItemNotFoundException: 用户不存在。
    """
    # 1. 先获取对象
    user_obj = await crud_user_account.get(db, user_id)

    if not user_obj:
        raise ItemNotFoundException(f"User with ID {user_id} not found.")

    # 2. 传入对象进行更新
    updated_user = await crud_user_account.update(db, db_obj=user_obj, max_databases=data.max_databases)

    return AdminUpdateUserQuotaResponse(
        user_id=updated_user.user_id,
        max_databases=updated_user.max_databases,
        updated_at=datetime.now()
    )


# ----------------------------------------------------------------------
# 公告管理
# ----------------------------------------------------------------------

async def create_announcement_service(
    db: AsyncSession,
    data: AnnouncementCreateRequest,
    admin_user_id: int
) -> AnnouncementResponse:
    """
    创建新公告。

    Args:
        db (AsyncSession): 数据库会话。
        data (AnnouncementCreateRequest): 公告创建请求体。
        admin_user_id (int): 创建者管理员用户 ID。

    Returns:
        AnnouncementResponse: 创建后的公告信息。
    """
    announcement_orm = await crud_announcement.create(db, created_by=admin_user_id, **data.model_dump())
    return AnnouncementResponse.model_validate(announcement_orm)


async def update_announcement_service(
    db: AsyncSession,
    announcement_id: int,
    data: AnnouncementUpdateRequest
) -> AnnouncementResponse:
    """
    更新公告内容或状态。

    Args:
        db (AsyncSession): 数据库会话。
        announcement_id (int): 公告 ID。
        data (AnnouncementUpdateRequest): 更新请求体。

    Returns:
        AnnouncementResponse: 更新后的公告信息。

    Raises:
        ItemNotFoundException: 公告不存在。
    """
    update_data = data.model_dump(exclude_unset=True)
    announcement_orm = await crud_announcement.update(db, announcement_id=announcement_id, update_data=update_data)
    if not announcement_orm:
        raise ItemNotFoundException("Announcement not found.")
    return AnnouncementResponse.model_validate(announcement_orm)


async def delete_announcement_service(db: AsyncSession, announcement_id: int) -> None:
    """
    删除公告。

    Args:
        db (AsyncSession): 数据库会话。
        announcement_id (int): 公告 ID。

    Raises:
        ItemNotFoundException: 公告不存在。
    """
    success = await crud_announcement.remove(db, announcement_id)
    if not success:
        raise ItemNotFoundException("Announcement not found.")


# ----------------------------------------------------------------------
# 系统状态
# ----------------------------------------------------------------------

async def get_admin_list_service(db: AsyncSession, page: int, page_size: int) -> AdminListResponse:
    """
    获取管理员列表。

    Args:
        db (AsyncSession): 数据库会话。
        page (int): 页码。
        page_size (int): 每页数量。

    Returns:
        AdminListResponse: 管理员分页列表。
    """
    admin_orms, total = await crud_admin_data.get_admin_list(db, page, page_size)
    
    # 手动构建 AdminListItem 对象，使用 Redis 中的在线状态
    items_dto = []
    for orm in admin_orms:
        # 将 datetime 转换为 ISO 格式字符串
        last_login_str = None
        if orm.last_login_at:
            last_login_str = orm.last_login_at.isoformat()
        
        # 从 Redis 获取实时在线状态
        from service.user_service import service_get_user_online_status
        is_online = await service_get_user_online_status(orm.user_id)
        
        item = AdminListItem(
            user_id=orm.user_id,
            username=orm.username,
            email=orm.email,
            avatar_url=orm.avatar_url,
            last_login_at=last_login_str,
            is_online=is_online,  # 使用 Redis 中的实时在线状态
        )
        items_dto.append(item)
    
    return AdminListResponse(total=total, page=page, page_size=page_size, items=items_dto)


async def get_violation_logs_service(
    db: AsyncSession,
    page: int,
    page_size: int,
    risk_level: Optional[str],
    resolution_status: Optional[str]
) -> ViolationLogListResponse:
    """
    获取违规记录列表。

    Args:
        db (AsyncSession): 数据库会话。
        page (int): 页码。
        page_size (int): 每页数量。
        risk_level (Optional[str]): 风险等级过滤。
        resolution_status (Optional[str]): 处置状态过滤。

    Returns:
        ViolationLogListResponse: 违规记录分页列表。
    """
    logs_data, total = await crud_admin_data.get_violation_logs(db, page, page_size, risk_level, resolution_status)
    items_dto = [ViolationLogListItem(**data) for data in logs_data]
    return ViolationLogListResponse(total=total, page=page, page_size=page_size, items=items_dto)


async def get_admin_stats_service(db: AsyncSession) -> AdminStatsResponse:
    """
    获取系统统计数据。

    Args:
        db (AsyncSession): 数据库会话。

    Returns:
        AdminStatsResponse: 统计看板数据。
    """
    stats_data = await crud_admin_data.get_system_stats(db)
    return AdminStatsResponse(**stats_data)


# ============================================================================
# 黑名单/频率限制管理功能
# ============================================================================

async def ban_user_service(
    db: AsyncSession,
    user_id: int,
    reason: str = "违反服务条款",
    admin_id: int = 0
) -> Dict[str, Any]:
    """
    管理员手动封禁用户。
    
    Args:
        db: 数据库会话
        user_id: 要封禁的用户ID
        reason: 封禁原因
        admin_id: 执行封禁的管理员ID
        
    Returns:
        包含操作结果的字典
    """
    try:
        from core.security import BlacklistManager
        from models.user_account import UserAccount
        
        # 检查用户是否存在
        result = await db.execute(
            select(UserAccount).where(UserAccount.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ItemNotFoundException(f"User with ID {user_id} not found")
        
        # 执行封禁
        success = await BlacklistManager.ban_user(
            db, user_id, reason=reason, banned_by=admin_id
        )
        
        if success:
            log.info(f"管理员 {admin_id} 手动封禁用户 {user_id}: {reason}")
            return {
                "success": True,
                "message": f"用户 {user_id} 已被封禁",
                "user_id": user_id,
                "reason": reason,
                "status": "banned",
            }
        else:
            return {
                "success": False,
                "message": f"封禁用户 {user_id} 失败",
            }
    
    except Exception as e:
        log.error(f"封禁用户失败: {e}")
        raise


async def unban_user_service(
    db: AsyncSession,
    user_id: int,
    admin_id: int = 0
) -> Dict[str, Any]:
    """
    管理员手动解封用户。
    
    Args:
        db: 数据库会话
        user_id: 要解封的用户ID
        admin_id: 执行解封的管理员ID
        
    Returns:
        包含操作结果的字典
    """
    try:
        from core.security import BlacklistManager, freq_limiter, login_failure_tracker
        from models.user_account import UserAccount
        
        # 检查用户是否存在
        result = await db.execute(
            select(UserAccount).where(UserAccount.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ItemNotFoundException(f"User with ID {user_id} not found")
        
        # 执行解封
        success = await BlacklistManager.unban_user(db, user_id, admin_id=admin_id)
        
        if success:
            # 重置请求频率
            freq_limiter.reset_frequency(user_id)
            # 重置登录失败计数（确保用户解封后可以正常登录）
            await login_failure_tracker.reset_failed_count(user_id)
            log.info(f"管理员 {admin_id} 手动解封用户 {user_id}，已重置登录失败计数")
            return {
                "success": True,
                "message": f"用户 {user_id} 已被解封",
                "user_id": user_id,
                "status": "normal",
            }
        else:
            return {
                "success": False,
                "message": f"解封用户 {user_id} 失败",
            }
    
    except Exception as e:
        log.error(f"解封用户失败: {e}")
        raise


async def get_banned_users_service(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    获取被封禁的用户列表。
    
    Args:
        db: 数据库会话
        page: 页码
        page_size: 每页数量
        
    Returns:
        包含被封禁用户列表的字典
    """
    try:
        from models.user_account import UserAccount
        from sqlalchemy import or_
        
        # 获取总数（包括 banned 和 suspended 状态的用户）
        count_result = await db.execute(
            select(UserAccount).where(
                or_(
                    UserAccount.status == 'banned',
                    UserAccount.status == 'suspended'
                )
            )
        )
        total_count = len(count_result.scalars().all())
        
        # 分页
        offset = (page - 1) * page_size
        result = await db.execute(
            select(UserAccount)
            .where(
                or_(
                    UserAccount.status == 'banned',
                    UserAccount.status == 'suspended'
                )
            )
            .order_by(desc(UserAccount.updated_at))
            .offset(offset)
            .limit(page_size)
        )
        users = result.scalars().all()
        
        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "users": [
                {
                    "user_id": u.user_id,
                    "username": u.username,
                    "email": u.email,
                    "status": u.status,
                    "status_desc": "管理员封禁" if u.status == 'banned' else "系统标记异常",
                    "updated_at": u.updated_at.isoformat() if u.updated_at else None,
                }
                for u in users
            ]
        }
    
    except Exception as e:
        log.error(f"获取被封禁用户列表失败: {e}")
        raise


async def get_violation_stats_service(
    db: AsyncSession,
    hours: int = 24
) -> Dict[str, Any]:
    """
    获取违规统计信息。
    
    Args:
        db: 数据库会话
        hours: 统计时间范围（小时）
        
    Returns:
        包含违规统计的字典
    """
    try:
        from models.violation_log import ViolationLog
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # 获取指定时间范围内的违规记录
        result = await db.execute(
            select(ViolationLog).where(
                ViolationLog.created_at >= cutoff_time
            )
        )
        logs = result.scalars().all()
        
        # 统计各风险等级的数量
        risk_stats = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
        }
        
        event_type_stats = {}
        
        for log in logs:
            risk_stats[log.risk_level] = risk_stats.get(log.risk_level, 0) + 1
            event_type_stats[log.event_type] = event_type_stats.get(log.event_type, 0) + 1
        
        return {
            "time_range_hours": hours,
            "total_violations": len(logs),
            "risk_level_distribution": risk_stats,
            "event_type_distribution": event_type_stats,
            "pending_violations": len([l for l in logs if l.resolution_status == "pending"]),
        }
    
    except Exception as e:
        log.error(f"获取违规统计失败: {e}")
        raise


async def get_frequency_limit_status_service(
    db: AsyncSession,
    user_id: int
) -> Dict[str, Any]:
    """
    获取用户的频率限制状态。
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        包含频率限制状态的字典
    """
    try:
        from core.security import freq_limiter, ViolationLogger
        from models.user_account import UserAccount
        
        # 检查用户是否存在
        result = await db.execute(
            select(UserAccount).where(UserAccount.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ItemNotFoundException(f"User with ID {user_id} not found")
        
        # 获取当前请求频率
        current_frequency = freq_limiter.get_frequency(user_id)
        
        # 获取违规记录数
        violation_count = await ViolationLogger.get_violation_count(
            db, user_id, time_hours=24
        )
        
        return {
            "user_id": user_id,
            "username": user.username,
            "current_frequency": current_frequency,
            "frequency_threshold": 20,
            "time_window_seconds": 10,
            "violation_count_24h": violation_count,
            "auto_suspend_threshold": 3,
            "status": user.status,
            "is_banned": user.status == 'banned',
            "is_suspended": user.status == 'suspended',
        }
    
    except Exception as e:
        log.error(f"获取频率限制状态失败: {e}")
        raise


async def reset_frequency_limit_service(
    db: AsyncSession,
    user_id: int,
    admin_id: int = 0
) -> Dict[str, Any]:
    """
    管理员重置用户的频率限制（清空 Redis 计数器）。
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        admin_id: 执行重置的管理员ID
        
    Returns:
        包含操作结果的字典
    """
    try:
        from core.security import freq_limiter
        from models.user_account import UserAccount
        
        # 检查用户是否存在
        result = await db.execute(
            select(UserAccount).where(UserAccount.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ItemNotFoundException(f"User with ID {user_id} not found")
        
        # 重置频率
        success = freq_limiter.reset_frequency(user_id)
        
        if success:
            log.info(f"管理员 {admin_id} 重置了用户 {user_id} 的频率限制")
            return {
                "success": True,
                "message": f"用户 {user_id} 的频率限制已重置",
                "user_id": user_id,
            }
        else:
            return {
                "success": False,
                "message": "重置频率限制失败",
            }
    
    except Exception as e:
        log.error(f"重置频率限制失败: {e}")
        raise
