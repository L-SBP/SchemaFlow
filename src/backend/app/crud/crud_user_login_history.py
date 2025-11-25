from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
        纯数据查询：获取用户最新的「登录成功且未登出」的记录
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
        纯数据操作：创建登录记录（登录接口专用）
        对齐表的必填字段（user_id、ip_address、login_status）
        
        :param db: 数据库会话
        :param user_id: 用户ID
        :param ip_address: IP地址
        :param login_status: 登录状态
        :param user_agent: 用户代理信息
        :param failure_reason: 失败原因
        :param device_info: 设备信息
        :param login_time: 登录时间
        :return: 用户登录历史记录对象
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
        纯数据更新：更新登录记录的登出信息（登出时间、会话时长、登录状态）
        
        :param db: 数据库会话
        :param login_history: 要更新的登录记录对象
        :param logout_time: 登出时间
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

crud_login_history = CRUDLoginHistory()
