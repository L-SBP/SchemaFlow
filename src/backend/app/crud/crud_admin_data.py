# backend/app/crud/crud_admin_data.py

from typing import List, Literal, Tuple, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from core.exceptions import DatabaseOperationFailedException

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


curd_admin_data = CRUDAdminData()