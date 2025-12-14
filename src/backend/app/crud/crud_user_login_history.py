"""
用户登录历史 CRUD。

本模块提供用于追踪用户登录历史的 CRUD 操作。
"""

# backend/app/crud/crud_user_login_history.py

from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from models.user_login_history import UserLoginHistory
from core.exceptions import DatabaseOperationFailedException
from core.log import log


class CRUDLoginHistory:
    @staticmethod
    async def get_latest_unlogout_record(
            db: AsyncSession, user_id: int
    ) -> UserLoginHistory | None:
        """
        获取用户最新的「登录成功且未登出」的记录。

        Args:
            db (AsyncSession): 数据库会话。
            user_id (int): 用户 ID。

        Returns:
            UserLoginHistory | None: 最新未登出的登录记录，若无则返回 None。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
        """
        try:
            query = (
                select(UserLoginHistory)
                .where(
                    UserLoginHistory.user_id == user_id,
                    UserLoginHistory.login_status == "success"
                )
                .order_by(UserLoginHistory.login_time.desc())
                .limit(1)
            )
            result = await db.execute(query)

            latest_record = result.scalars().first()
            log.debug(f"get latest unlogout record: {latest_record}")

            return latest_record
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("get latest unlogout record") from e

    @staticmethod
    async def create_login_record(
            db: AsyncSession,
            user_id: Optional[int],
            ip_address: str,
            login_status: str,
            user_agent: str | None = None,
            failure_reason: str | None = None,
            device_info: dict | None = None,
            login_time: datetime | None = None
    ) -> UserLoginHistory:
        """
        创建登录记录（登录接口专用）。

        对齐表的必填字段（user_id、ip_address、login_status）。

        Args:
            db (AsyncSession): 数据库会话。
            user_id (Optional[int]): 用户ID。
            ip_address (str): IP地址。
            login_status (str): 登录状态。
            user_agent (str | None): 用户代理信息。
            failure_reason (str | None): 失败原因。
            device_info (dict | None): 设备信息。
            login_time (datetime | None): 登录时间。

        Returns:
            UserLoginHistory: 用户登录历史记录对象。

        Raises:
            DatabaseOperationFailedException: 创建失败时抛出。
        """
        try:
            db_obj = UserLoginHistory(
                user_id=user_id,
                login_time=login_time or datetime.now(timezone.utc),
                ip_address=ip_address,
                user_agent=user_agent,
                login_status=login_status,
                failure_reason=failure_reason,
                device_info=device_info,
                created_at=datetime.now(timezone.utc)
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("create login record") from e

    @staticmethod
    async def update_logout_info(
        db: AsyncSession,
        login_history: UserLoginHistory,  # 要更新的登录记录对象
        logout_time: datetime = datetime.now(timezone.utc)
    ) -> None:
        """
        更新登录记录的登出信息（登出时间、会话时长、登录状态）。

        Args:
            db (AsyncSession): 数据库会话。
            login_history (UserLoginHistory): 要更新的登录记录对象。
            logout_time (datetime): 登出时间。

        Raises:
            DatabaseOperationFailedException: 更新失败时抛出。
        """
        try:
            # 只做数据赋值，不做业务判断（业务判断在Service层）
            login_history.logout_time = logout_time
            login_history.session_duration = logout_time - login_history.login_time
            login_history.login_status = "forced_logout"
            await db.commit()
            await db.refresh(login_history)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("update logout info") from e

    # 新增添加分页查询方法
    @staticmethod
    async def get_multi_by_user(
            db: AsyncSession,
            user_id: int,
            skip: int = 0,
            limit: int = 10
    ) -> Tuple[List[UserLoginHistory], int]:
        """
        获取用户的登录历史列表（支持分页）。

        Args:
            db (AsyncSession): 数据库会话。
            user_id (int): 用户 ID。
            skip (int): 跳过的记录数。
            limit (int): 返回的最大记录数。

        Returns:
            Tuple[List[UserLoginHistory], int]: (记录列表, 总数)。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
        """
        try:
            # 1. 查询总数
            count_query = select(func.count(UserLoginHistory.login_id)).where(
                UserLoginHistory.user_id == user_id
            )
            total_result = await db.execute(count_query)
            total = total_result.scalar_one()

            # 2. 查询列表数据 (按登录时间倒序)
            query = (
                select(UserLoginHistory)
                .where(UserLoginHistory.user_id == user_id)
                .order_by(desc(UserLoginHistory.login_time))
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(query)
            items = result.scalars().all()

            return items, total
        except SQLAlchemyError as e:
            # 这里的异常会被 Service 层或 Router 层的通用异常处理捕获
            raise DatabaseOperationFailedException("get login history list") from e

crud_login_history = CRUDLoginHistory()
