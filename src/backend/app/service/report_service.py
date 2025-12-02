# backend/app/service/report_service.py

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession as Session
from fastapi import HTTPException

from crud.crud_report import crud_report
from schema import report as schemas
from core.exceptions import DatabaseOperationFailedException, ItemNotFoundException
from models.project import Project
from sqlalchemy import select

# --------------------------
# 1. 获取报表列表
# --------------------------
async def get_report_list(db: Session, project_id: int) -> List[schemas.Report]:

    db_objs = await crud_report.get_by_project(db, project_id)
    reports = []

    for obj in db_objs:

        default_chart_config = schemas.ChartConfig(
            xAxisKey="name",
            yAxisKey="value"
        )

        report_data = obj.result_data if isinstance(obj.result_data, list) else []

        report = schemas.Report(
            id=str(obj.result_id),
            projectId=str(project_id),
            name=obj.data_summary[:20] if obj.data_summary else f"Report-{obj.result_id}",
            type=obj.chart_type or "table",
            description=obj.data_summary,
            data=report_data,
            sourceQueryText="SELECT * FROM ...",
            updatedAt=obj.cached_at.isoformat() if obj.cached_at else ""
        )
        reports.append(report)

    return reports


# --------------------------
# 2. 获取报表详情
# --------------------------
async def get_report_data_by_id_service(db: Session, query_id: int) -> Dict[str, Any]:

    raw = await crud_report.get_report_data_by_result_id(db, query_id)

    if not raw:
        raise ItemNotFoundException(f"Query result with ID {query_id} not found.")

    query_result, statement = raw

    return {
        "result_data": query_result.result_data,
        "data_summary": query_result.data_summary,
        "chart_type": query_result.chart_type,
        "sql_text": statement.sql_text,
        "cached_at": query_result.cached_at.isoformat() if query_result.cached_at else None
    }


# --------------------------
# 3. 获取历史查询记录
# --------------------------
async def get_history_queries_service(db: Session, project_id: int) -> List[schemas.HistoryQuery]:

    db_objs = await crud_report.get_history_by_project(db, project_id)
    history = []

    for obj in db_objs:
        history.append(schemas.HistoryQuery(
    id=str(obj.result_id),
    projectId=str(project_id),  # ← 修复类型错误
    queryText=obj.data_summary or "N/A",
    timestamp=obj.cached_at.isoformat() if obj.cached_at else 'N/A',
    result=obj.result_data
))
        

    return history


# --------------------------
# 4. 创建报表（实时渲染，不入库）
# --------------------------
async def create_report_service(db: Session, project_id: int, payload: schemas.ReportCreate):

    project_exists = await db.execute(select(Project).where(Project.project_id == project_id))
    if not project_exists.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found")
    raw = await crud_report.get_report_data_by_result_id(db, payload.query_id)
    if not raw:
        raise HTTPException(status_code=404, detail="Query result not found")

    query_result, statement = raw

    return schemas.Report(
        id=str(query_result.result_id),
        projectId=str(project_id),
        name=payload.report_name,
        type=payload.chart_type,
        description=query_result.data_summary,
        data=query_result.result_data,
        chartConfig=payload.chartConfig,
        sourceQueryText=statement.sql_text,
        updatedAt=query_result.cached_at.isoformat() if query_result.cached_at else ""
    )



# --------------------------
# 6. 导出报表
# --------------------------
async def export_report_service(db: Session, report_id: int, format: str):

    if format not in ("png", "pdf"):
        raise HTTPException(status_code=400, detail="format must be png or pdf")

    # 检查 report 是否存在
    raw = await crud_report.get_report_data_by_result_id(db, report_id)
    if not raw:
        raise HTTPException(status_code=404, detail="Report not found")

    # 正常返回
    return {
        "download_url": f"https://fake-cdn.example.com/reports/{report_id}.{format}",
        "expires_at": "2025-12-01T15:00:00Z"
    }

