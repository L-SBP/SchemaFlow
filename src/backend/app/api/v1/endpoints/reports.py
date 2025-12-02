# backend/app/api/v1/endpoints/reports.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from schema.report import ReportCreate, Report, HistoryQuery, UpdateChartType
from api.v1.deps import get_db
from service import report_service

router = APIRouter()

# 4.1 获取报表列表
@router.get("/reports", response_model=list[Report])
async def read_reports(
    projectId: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    return await report_service.get_report_list(db, projectId)


# 4.4 获取历史查询记录
@router.get("/history-queries", response_model=list[HistoryQuery])
async def read_history(
    projectId: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    return await report_service.get_history_queries_service(db, projectId)


# 3.5.1 创建报表（实时渲染）
@router.post("/projects/{project_id}/reports", response_model=Report)
async def create_report(
    project_id: int,
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
):
    return await report_service.create_report_service(db, project_id, body)


# 3.5.2 修改图表类型（已删除该接口）



# 3.5.3 导出报表
@router.get("/reports/{report_id}/export", response_model=dict)
async def export_report(
    report_id: int,
    format: str = Query("png"),
    db: AsyncSession = Depends(get_db)
):
    return await report_service.export_report_service(db, report_id, format)
