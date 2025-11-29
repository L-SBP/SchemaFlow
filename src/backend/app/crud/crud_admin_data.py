# backend/app/crud/crud_admin_data.py

from typing import List, Literal, Tuple, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from core.exceptions import DatabaseOperationFailedException
from datetime import datetime  # 【新增】添加这一行导入
from sqlalchemy import desc

# 假设导入 ORM 模型
from models.user_account import UserAccount
from models.project import Project
from models.violation_log import ViolationLog


class CRUDAdminData:

    # ------------------------------------------------------------------
    # 4.1.1. 获取用户列表
    # ------------------------------------------------------------------

    @staticmethod
    async def get_user_list_with_stats(db: AsyncSession, page: int, page_size: int, search: Optional[str] = None,
                                       status: Literal["normal", "banned", "all"] = "all") -> Tuple[
        List[Dict[str, Any]], int]:
        """获取用户列表，包含项目统计和额度。"""
        # 实际代码应实现复杂的 JOIN 和筛选逻辑 (如前分析)
        # Mocking the data structure return:
        items = [{
            "user_id": 1002, "username": "admin_user", "email": "admin@example.com", "status": "banned",
            "max_databases": 10, "project_count": 5, "last_login_at": datetime.now()
        }]
        return items, 100

        # ------------------------------------------------------------------

    # 4.3.1. 获取管理员列表
    # ------------------------------------------------------------------
    @staticmethod
    async def get_admin_list(db: AsyncSession, page: int, page_size: int) -> Tuple[List[UserAccount], int]:
        """获取所有管理员列表"""
        # 实际代码应 SELECT UserAccount.is_admin == True
        # Mocking the data structure return:
        return [UserAccount(user_id=1, username='admin', email='a@e.com', is_admin=True)], 1

    # ------------------------------------------------------------------
    # 4.4.1. 获取系统统计
    # ------------------------------------------------------------------
    @staticmethod
    async def get_system_stats(db: AsyncSession) -> Dict[str, Any]:
        """获取系统统计看板数据"""
        # 实际代码应包含多表聚合查询
        return {
            "active_users_today": 150, "total_projects": 500, "query_count_today": 2500,
            "high_risk_operations_today": 15, "system_health": "good"
        }

    # 添加这个缺失的方法
    @staticmethod
    async def get_violation_logs(
            db: AsyncSession,
            page: int,
            page_size: int,
            risk_level: Optional[str] = None,
            resolution_status: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取违规记录列表 (支持分页、筛选，并关联用户名)
        """
        # 1. 构建基础查询：关联 UserAccount 表以获取 username
        query = select(ViolationLog, UserAccount.username) \
            .join(UserAccount, ViolationLog.user_id == UserAccount.user_id)

        count_query = select(func.count(ViolationLog.violation_id))

        # 2. 动态添加筛选条件
        filters = []
        if risk_level:
            filters.append(ViolationLog.risk_level == risk_level)
        if resolution_status:
            filters.append(ViolationLog.resolution_status == resolution_status)

        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)

        # 3. 执行总数查询
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # 4. 执行分页查询 (按时间倒序)
        query = query.order_by(desc(ViolationLog.created_at)) \
            .offset((page - 1) * page_size) \
            .limit(page_size)

        result = await db.execute(query)
        rows = result.all()

        # 5. 格式化返回数据
        items = []
        for log_obj, username in rows:
            items.append({
                "violation_id": log_obj.violation_id,
                "user_id": log_obj.user_id,
                "username": username,  # 前端需要展示用户名
                "risk_level": log_obj.risk_level,
                "resolution_status": log_obj.resolution_status,
                "created_at": log_obj.created_at
            })

        return items, total


curd_admin_data = CRUDAdminData()