# backend/app/crud/crud_admin_data.py

from typing import List, Literal, Tuple, Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, desc, cast, Date

from core.exceptions import DatabaseOperationFailedException

# 导入所有需要的模型
from models.user_account import UserAccount
from models.project import Project
from models.violation_log import ViolationLog
from models.user_login_history import UserLoginHistory
from models.ai_generated_statement import AIGeneratedStatement


class CRUDAdminData:

    # ------------------------------------------------------------------
    # 4.1.1. 获取用户列表 (带统计数据)
    # ------------------------------------------------------------------
    @staticmethod
    async def get_user_list_with_stats(
            db: AsyncSession,
            page: int,
            page_size: int,
            search: Optional[str] = None,
            status: Literal["normal", "banned", "all"] = "all"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取用户列表，包含项目统计和额度。
        实现逻辑：查询 UserAccount 表，并 Left Join Project 表计算 count。
        """
        try:
            # 1. 构建基础查询：选择用户列 + 项目计数
            # SELECT u.*, count(p.project_id) FROM user_account u LEFT JOIN project p ON ...
            stmt = (
                select(
                    UserAccount,
                    func.count(Project.project_id).label("project_count")
                )
                .outerjoin(Project, UserAccount.user_id == Project.user_id)
                .group_by(UserAccount.user_id)
            )

            # 2. 构建 Count 查询 (用于分页总数)
            count_stmt = select(func.count(UserAccount.user_id))

            # 3. 应用筛选条件
            filters = []
            if status != "all":
                filters.append(UserAccount.status == status)

            if search:
                search_term = f"%{search}%"
                filters.append(
                    or_(
                        UserAccount.username.ilike(search_term),
                        UserAccount.email.ilike(search_term)
                    )
                )

            if filters:
                stmt = stmt.where(*filters)
                count_stmt = count_stmt.where(*filters)

            # 4. 执行总数查询
            total = await db.scalar(count_stmt) or 0

            # 5. 执行分页查询 (按注册时间倒序)
            stmt = stmt.order_by(desc(UserAccount.created_at)).offset((page - 1) * page_size).limit(page_size)
            result = await db.execute(stmt)
            rows = result.all()

            # 6. 组装返回数据 (将 ORM 对象转为字典，并合并且它的统计数据)
            items = []
            for user, project_count in rows:
                items.append({
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "status": user.status,
                    "max_databases": user.max_databases,
                    "last_login_at": user.last_login_at,
                    "project_count": project_count  # 聚合查询出来的字段
                })

            return items, total

        except Exception as e:
            raise DatabaseOperationFailedException("fetch user list with stats") from e

    # ------------------------------------------------------------------
    # 4.3.1. 获取管理员列表
    # ------------------------------------------------------------------
    @staticmethod
    async def get_admin_list(db: AsyncSession, page: int, page_size: int) -> Tuple[List[UserAccount], int]:
        """获取所有管理员列表"""
        try:
            # 1. 筛选条件
            query = select(UserAccount).where(UserAccount.is_admin == True)
            count_query = select(func.count(UserAccount.user_id)).where(UserAccount.is_admin == True)

            # 2. 获取总数
            total = await db.scalar(count_query) or 0

            # 3. 分页查询
            query = query.order_by(desc(UserAccount.created_at)).offset((page - 1) * page_size).limit(page_size)
            result = await db.execute(query)
            admins = result.scalars().all()

            return admins, total
        except Exception as e:
            raise DatabaseOperationFailedException("fetch admin list") from e

    # ------------------------------------------------------------------
    # 4.4.1. 获取系统统计
    # ------------------------------------------------------------------
    @staticmethod
    async def get_system_stats(db: AsyncSession) -> Dict[str, Any]:
        """获取系统统计看板数据 (真实数据库聚合)"""
        try:
            today = datetime.now().date()

            # 1. 今日活跃用户 (今日有登录记录的去重用户数)
            # 注意：SQLAlchemy 中 date 类型转换通常用 cast(col, Date)
            active_users_query = select(func.count(func.distinct(UserLoginHistory.user_id))) \
                .where(cast(UserLoginHistory.login_time, Date) == today)
            active_users_today = await db.scalar(active_users_query) or 0

            # 2. 项目总数
            total_projects_query = select(func.count(Project.project_id))
            total_projects = await db.scalar(total_projects_query) or 0

            # 3. 今日查询数 (AI 生成语句的数量作为近似值)
            query_count_query = select(func.count(AIGeneratedStatement.statement_id)) \
                .where(cast(AIGeneratedStatement.created_at, Date) == today)
            query_count_today = await db.scalar(query_count_query) or 0

            # 4. 今日高风险操作 (ViolationLog 中 risk_level 为 HIGH 或 CRITICAL)
            high_risk_query = select(func.count(ViolationLog.violation_id)) \
                .where(
                cast(ViolationLog.created_at, Date) == today,
                ViolationLog.risk_level.in_(['HIGH', 'CRITICAL'])
            )
            high_risk_ops = await db.scalar(high_risk_query) or 0

            # 5. 计算系统健康度 (简单逻辑)
            system_health = "good"
            if high_risk_ops > 10:
                system_health = "critical"
            elif high_risk_ops > 0:
                system_health = "warning"

            return {
                "active_users_today": active_users_today,
                "total_projects": total_projects,
                "query_count_today": query_count_today,
                "high_risk_operations_today": high_risk_ops,
                "system_health": system_health
            }
        except Exception as e:
            # 统计失败不应阻塞主流程，可以返回全0或抛出异常，这里选择抛出
            raise DatabaseOperationFailedException("fetch system stats") from e

    # ------------------------------------------------------------------
    # 4.4.2. 获取违规日志 (复用之前修复的代码)
    # ------------------------------------------------------------------
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
        try:
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
            total = await db.scalar(count_query) or 0

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
                    "username": username,
                    "risk_level": log_obj.risk_level,
                    "resolution_status": log_obj.resolution_status,
                    "created_at": log_obj.created_at
                })

            return items, total
        except Exception as e:
            raise DatabaseOperationFailedException("fetch violation logs") from e


curd_admin_data = CRUDAdminData()