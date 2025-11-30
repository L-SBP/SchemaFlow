# backend/app/service/report_service.py

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession as Session
from fastapi import HTTPException

# 导入 CRUD 和 Schema
from crud.crud_report import crud_report
from schema import report as schemas
from core.exceptions import DatabaseOperationFailedException, ItemNotFoundException

# 1. 获取报表列表
async def get_report_list(db: Session, project_id: int) -> List[schemas.Report]:
    """
    业务逻辑：获取报表列表。
    需要将 DB 中的 QueryResult 对象转换为 Schema 中的 Report 对象。
    """
    # 1. 获取数据库对象列表
    db_objs = await crud_report.get_by_project(db, project_id)

    reports = []
    for obj in db_objs:
        # 2. 手动构造 Report 对象 (字段映射)

        # 构造默认图表配置 (因为目前 DB 里没有存详细配置)
        default_chart_config = schemas.ChartConfig(
            xAxisKey="name",
            yAxisKey="value"
        )

        # 确保 data 是列表格式
        report_data = obj.result_data if isinstance(obj.result_data, list) else []

        # 映射字段: ORM -> Schema
        report = schemas.Report(
            id=str(obj.result_id),                  # result_id -> id
            projectId=str(project_id),              # 传入的 project_id
            name=obj.data_summary[:20] if obj.data_summary else f"Report-{obj.result_id}", # 使用摘要做标题
            type=obj.chart_type or "table",         # chart_type -> type
            description=obj.data_summary,           # data_summary -> description
            data=report_data,                       # result_data -> data
            chartConfig=default_chart_config,       # 填充必填项
            sourceQueryText="SELECT * FROM ...",    # 暂无 SQL 文本，填占位符
            updatedAt=obj.cached_at.isoformat() if obj.cached_at else "" # cached_at -> updatedAt
        )
        reports.append(report)

    return reports

# 2. 获取报表详情数据 (从 project_service.py 移过来的)
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

# 3. 获取历史查询 (从 project_service.py 移过来的)
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