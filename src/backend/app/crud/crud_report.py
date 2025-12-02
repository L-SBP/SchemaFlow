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
    CRUD: 负责从现有表 (query_result, ai_generated_statement) 中提取数据
    """

    @staticmethod
    async def get_report_data_by_result_id(db: Session, result_id: int) -> Optional[
        Tuple[QueryResult, AIGeneratedStatement]]:
        """
        CRUD: 根据 result_id 查找查询结果及其关联的 SQL 语句。
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
        CRUD: 根据项目ID获取历史查询结果列表（用于列表接口）。
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
        CRUD: 获取项目报表列表 (修正版：增加 Project 筛选)
        路径: QueryResult -> Statement -> Message -> Session -> Project
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
        更新报表的图表类型 -> 实际更新 QueryResult.chart_type 字段
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