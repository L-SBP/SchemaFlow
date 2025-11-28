# backend/app/crud/crud_report.py

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy.future import select
from sqlalchemy import join
from sqlalchemy.exc import SQLAlchemyError

# 隐式绝对导入
from models.query_result import QueryResult  # 缓存结果表
from models.ai_generated_statement import AIGeneratedStatement
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
    async def get_history_by_project(db: Session, project_id: str) -> List[QueryResult]:
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


crud_report = CRUDReport()