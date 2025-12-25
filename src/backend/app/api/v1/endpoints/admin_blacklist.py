"""
管理员黑名单管理 API 端点。

提供管理员用户封禁、解封、频率限制监控等功能的 REST API。
"""

# backend/app/api/v1/endpoints/admin_blacklist.py

from typing import Optional
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_db, get_current_admin
from core.log import log
from models.user_account import UserAccount
from core.exceptions import ItemNotFoundException, ValidationException
from service.admin_service import (
    ban_user_service,
    unban_user_service,
    get_banned_users_service,
    get_violation_stats_service,
    get_frequency_limit_status_service,
    reset_frequency_limit_service,
)

# 创建路由器
router = APIRouter(
    prefix="/api/v1/admin/blacklist",
    tags=["Admin - Blacklist Management"],
    dependencies=[Depends(get_current_admin)]
)


# ============================================================================
# 1. 用户黑名单操作
# ============================================================================

@router.post("/ban/{user_id}")
async def ban_user(
    user_id: int,
    reason: str = "违反服务条款",
    current_admin: UserAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员手动封禁用户。
    
    触发条件：
    - 管理员主动封禁
    - 自动三击机制触发
    
    参数：
    - user_id: 要封禁的用户ID
    - reason: 封禁原因（可选，默认"违反服务条款"）
    
    返回：
    {
        "success": true,
        "message": "用户 123 已被封禁",
        "user_id": 123,
        "reason": "违反服务条款",
        "banned_at": "2025-12-23T10:30:00+00:00"
    }
    """
    return await ban_user_service(
        db=db,
        user_id=user_id,
        reason=reason,
        admin_id=current_admin.user_id
    )


@router.post("/unban/{user_id}")
async def unban_user(
    user_id: int,
    current_admin: UserAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员手动解封用户。
    
    效果：
    - 将用户 is_active 设为 True
    - 清空 Redis 频率限制计数器
    - 清空封禁原因
    
    参数：
    - user_id: 要解封的用户ID
    
    返回：
    {
        "success": true,
        "message": "用户 123 已被解封",
        "user_id": 123
    }
    """
    return await unban_user_service(
        db=db,
        user_id=user_id,
        admin_id=current_admin.user_id
    )


@router.get("/list")
async def list_banned_users(
    page: int = 1,
    page_size: int = 20,
    current_admin: UserAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取被封禁的用户列表。
    
    分页查询所有已被封禁（is_active=False）的用户。
    
    参数：
    - page: 页码（从 1 开始），默认 1
    - page_size: 每页数量，默认 20，最大 100
    
    返回：
    {
        "total": 5,
        "page": 1,
        "page_size": 20,
        "users": [
            {
                "user_id": 123,
                "username": "violator_user",
                "email": "user@example.com",
                "banned_at": "2025-12-23T10:30:00+00:00",
                "ban_reason": "过度API调用"
            },
            ...
        ]
    }
    """
    # 参数验证
    page = max(1, page)
    page_size = min(max(1, page_size), 100)  # 限制最大 100
    
    return await get_banned_users_service(
        db=db,
        page=page,
        page_size=page_size
    )


# ============================================================================
# 2. 频率限制和违规监控
# ============================================================================

@router.get("/frequency/{user_id}")
async def get_frequency_status(
    user_id: int,
    current_admin: UserAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的频率限制状态。
    
    包含：
    - 当前请求频率（Redis 计数器）
    - 频率阈值和时间窗口
    - 24小时内的违规记录数
    - 是否被封禁
    - 封禁原因（如果已封禁）
    
    参数：
    - user_id: 用户ID
    
    返回：
    {
        "user_id": 123,
        "username": "test_user",
        "current_frequency": 5,
        "frequency_threshold": 20,
        "time_window_seconds": 10,
        "violation_count_24h": 2,
        "auto_ban_threshold": 3,
        "is_banned": false,
        "ban_reason": null
    }
    """
    result = await get_frequency_limit_status_service(
        db=db,
        user_id=user_id
    )
    return result


@router.post("/frequency/{user_id}/reset")
async def reset_frequency(
    user_id: int,
    current_admin: UserAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    重置用户的频率限制计数器。
    
    效果：
    - 清空 Redis 中的 user:freq:{user_id} 键
    - 允许用户继续使用 API
    
    参数：
    - user_id: 用户ID
    
    返回：
    {
        "success": true,
        "message": "用户 123 的频率限制已重置",
        "user_id": 123
    }
    """
    result = await reset_frequency_limit_service(
        db=db,
        user_id=user_id,
        admin_id=current_admin.user_id
    )
    return result


@router.get("/violations/stats")
async def get_violation_statistics(
    hours: int = 24,
    current_admin: UserAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取违规统计信息。
    
    统计指定时间范围内的所有违规事件，按风险等级和事件类型分类。
    
    参数：
    - hours: 统计时间范围（小时），默认 24
    
    返回：
    {
        "time_range_hours": 24,
        "total_violations": 15,
        "risk_level_distribution": {
            "CRITICAL": 2,
            "HIGH": 5,
            "MEDIUM": 6,
            "LOW": 2
        },
        "event_type_distribution": {
            "excessive_api_usage": 8,
            "sql_injection_attempt": 2,
            "suspicious_query": 3,
            "unauthorized_access_attempt": 2
        },
        "pending_violations": 10
    }
    """
    # 参数验证
    hours = max(1, min(hours, 720))  # 限制 1-30 天
    
    result = await get_violation_stats_service(
        db=db,
        hours=hours
    )
    return result


# ============================================================================
# 3. 批量操作和报告
# ============================================================================

@router.get("/dashboard")
async def get_blacklist_dashboard(
    current_admin: UserAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取黑名单管理看板数据。
    
    综合显示：
    - 被封禁用户总数
    - 24小时内的违规统计
    - 风险等级分布
    - 事件类型分布
    
    返回：
    {
        "banned_users_count": 5,
        "violation_stats": {
            "time_range_hours": 24,
            "total_violations": 15,
            "risk_level_distribution": {...},
            "event_type_distribution": {...},
            "pending_violations": 10
        },
        "timestamp": "2025-12-23T10:30:00+00:00"
    }
    """
    from datetime import datetime, timezone
    
    # 获取被封禁用户数
    banned_users_response = await get_banned_users_service(
        db=db,
        page=1,
        page_size=1
    )
    banned_users_count = banned_users_response.get("total", 0)
    
    # 获取违规统计
    violation_stats = await get_violation_stats_service(
        db=db,
        hours=24
    )
    
    return {
        "banned_users_count": banned_users_count,
        "violation_stats": violation_stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
