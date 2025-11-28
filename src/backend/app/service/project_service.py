# backend/app/service/project_service.py

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession as Session

# 隐式绝对导入
from crud.crud_report import crud_report  # 导入 CRUD 层
from schema import report as schemas  # 导入 Schema DTOs
from core.exceptions import DatabaseOperationFailedException, ItemNotFoundException


async def get_report_data_by_id_service(db: Session, query_id: int) -> Dict[str, Any]:
    """
    Service 逻辑：
    1. 调用 CRUD 提取 QueryResult 和 Statement。
    2. 将原始 ORM 数据转换为前端渲染所需的 JSON 格式。
    """
    try:
        # 1. 调用 CRUD 获取原始数据
        raw_data = await crud_report.get_report_data_by_result_id(db, query_id)

        if not raw_data:
            raise ItemNotFoundException(f"Query result with ID {query_id} not found.")

        query_result, statement = raw_data

        # 2. 业务处理/映射：构建前端渲染所需的 JSON 结构
        return {
            # 前端渲染所需的数据和配置
            "result_data": query_result.result_data,
            "data_summary": query_result.data_summary,
            "chart_type": query_result.chart_type,
            "sql_text": statement.sql_text,
            "cached_at": query_result.cached_at.isoformat() if query_result.cached_at else None
        }

    except DatabaseOperationFailedException as e:
        raise HTTPException(status_code=500, detail=f"Database error fetching data: {e}")


async def get_history_queries_service(db: Session, project_id: str) -> List[schemas.HistoryQuery]:
    """
    Service 逻辑：获取历史查询记录列表，并转换为 HistoryQuery DTO。
    """
    try:
        db_objs = await crud_report.get_history_by_project(db, project_id)

        # 转换为 HistoryQuery DTO
        history_dto = []
        for obj in db_objs:
            # 严格按照 HistoryQuery Schema (包含 id, queryText, result) 映射
            history_dto.append(schemas.HistoryQuery(
                id=str(obj.result_id),
                projectId=project_id,
                queryText=obj.data_summary or "N/A",  # 假设 data_summary 作为查询文本的预览
                timestamp=obj.cached_at.isoformat() if obj.cached_at else 'N/A',
                result=obj.result_data  # 将 JSONB 快照直接映射到 result 字段
            ))

        return history_dto

    except DatabaseOperationFailedException as e:
        raise HTTPException(status_code=500, detail=f"Database error fetching history: {e}")