"""
报表 CRUD。

本模块提供分析报表和查询结果的 CRUD 操作。
"""

# backend/app/crud/crud_report.py

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy.future import select
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update
# 导入所有相关模型以建立连接路径
from models.query_result import QueryResult
from models.ai_generated_statement import AIGeneratedStatement
from models.message import Message
from models.session import Session as SessionModel # 别名避免与 DB Session 混淆

from core.exceptions import DatabaseOperationFailedException


class CRUDReport:
    """
    报表数据操作类。

    负责从 query_result, ai_generated_statement 等表中提取数据。
    """

    @staticmethod
    async def get_report_data_by_result_id(db: Session, result_id: int) -> Optional[
        Tuple[QueryResult, AIGeneratedStatement]]:
        """
        根据 result_id 查找查询结果及其关联的 SQL 语句。

        Args:
            db (Session): 数据库会话。
            result_id (int): 结果 ID。

        Returns:
            Optional[Tuple[QueryResult, AIGeneratedStatement]]: 查询结果与语句的元组，若未找到则返回 None。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
        """
        try:
            # 这是一个复杂的 JOIN 查询
            query = select(QueryResult, AIGeneratedStatement).join(
                AIGeneratedStatement,QueryResult.statement_id == AIGeneratedStatement.statement_id
            ).where(QueryResult.result_id == result_id)

            result = await db.execute(query)
            return result.one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get report data by result_id") from e

    @staticmethod
    async def get_history_by_project(db: Session, project_id: int) -> List[QueryResult]:
        """
        根据项目ID获取历史查询结果列表（用于列表接口）。

        Args:
            db (Session): 数据库会话。
            project_id (int): 项目 ID。

        Returns:
            List[QueryResult]: 查询结果列表。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
        """
        try:
            # 实际查询需要 JOIN project, session, message, statement 来过滤 project_id
            # 这里简化为只查询 QueryResult
            query = select(QueryResult).order_by(QueryResult.cached_at.desc())
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get history queries by project") from e

    @staticmethod
    async def get_by_project(db: Session, project_id: int) -> List[QueryResult]:
        """
        获取项目报表列表。

        路径: QueryResult -> Statement -> Message -> Session -> Project

        Args:
            db (Session): 数据库会话。
            project_id (int): 项目 ID。

        Returns:
            List[QueryResult]: 查询结果列表。

        Raises:
            DatabaseOperationFailedException: 查询失败时抛出。
        """
        try:
            query = (
                select(QueryResult)
                .join(AIGeneratedStatement, QueryResult.statement_id == AIGeneratedStatement.statement_id)
                .join(Message, AIGeneratedStatement.message_id == Message.message_id)
                .join(SessionModel, Message.session_id == SessionModel.session_id)
                .where(SessionModel.project_id == project_id)  # 核心筛选条件
                .order_by(desc(QueryResult.cached_at))
            )

            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DatabaseOperationFailedException("get reports by project") from e

    # 兼容旧代码调用
    get_history_by_project = get_by_project

    @staticmethod
    async def update_chart_type(db: Session, result_id: int, chart_type: str):
        """
        更新报表的图表类型。

        Args:
            db (Session): 数据库会话。
            result_id (int): 结果 ID。
            chart_type (str): 新的图表类型。

        Returns:
            Optional[QueryResult]: 更新后的查询结果对象。

        Raises:
            DatabaseOperationFailedException: 更新失败时抛出。
        """
        try:
            query = (
                update(QueryResult)
                .where(QueryResult.result_id == result_id)
                .values(chart_type=chart_type)
                .returning(QueryResult)
            )

            result = await db.execute(query)
            obj = result.scalar_one_or_none()
            await db.commit()
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseOperationFailedException("update chart type failed") from e

crud_report = CRUDReport()