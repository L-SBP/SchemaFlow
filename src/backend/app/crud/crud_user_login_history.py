from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from models.user_login_history import UserLoginHistory
from core.exceptions import DatabaseOperationFailedException

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
            return result.scalars().first()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException() from e

    @staticmethod
    async def create_login_record(
            db: AsyncSession,
            user_id: int,
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
            raise DatabaseOperationFailedException() from e

    @staticmethod
    async def update_logout_info(
        db: AsyncSession,
        login_history: UserLoginHistory,  # 要更新的登录记录对象
        logout_time: datetime = datetime.now(timezone.utc)
    ) -> None:
        """
        纯数据更新：更新登录记录的登出信息（登出时间、会话时长、登录状态）
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
            raise DatabaseOperationFailedException() from e

crud_login_history = CRUDLoginHistory()