# backend/app/api/v1/endpoints/reports.py

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# 导入正确的 ReportUpdate Schema
from schema.report import ReportCreate, Report, HistoryQuery, ReportUpdate 
from api.v1.deps import get_db
from service import report_service

router = APIRouter()

# -------------------------------------------
# 1. 获取报表列表 (Read)
# -------------------------------------------
@router.get("/reports", response_model=List[Report])
async def read_reports(
    projectId: int = Query(..., description="项目ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定项目下的所有保存的报表配置。
    """
    return await report_service.get_report_list(db, projectId)

# -------------------------------------------
# 2. 获取历史查询记录
# -------------------------------------------
@router.get("/history-queries", response_model=List[HistoryQuery])
async def read_history(
    projectId: int = Query(..., description="项目ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取历史查询结果，用于作为创建新报表的数据源。
    """
    return await report_service.get_history_queries_service(db, projectId)

# -------------------------------------------
# 3. 创建报表 (Create)
# -------------------------------------------
@router.post("/projects/{project_id}/reports", response_model=Report)
async def create_report(
    project_id: int,
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    保存报表配置。
    """
    return await report_service.create_report_service(db, project_id, body)

# -------------------------------------------
# 4. 删除报表 (Delete)
# -------------------------------------------
@router.delete("/reports/{report_id}", response_model=bool)
async def delete_report(
    report_id: int = Path(..., description="报表ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    删除指定的报表配置。
    """
    success = await report_service.delete_report_service(db, report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    return True

# -------------------------------------------
# 5. 修改报表信息 (Update) - [已修复]
# -------------------------------------------
@router.put("/reports/{report_id}", response_model=Report)
async def update_report(
    body: ReportUpdate,  # 注意：Pydantic模型通常放在 Depends 前面
    report_id: int = Path(..., description="报表ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    修改报表配置（例如：修改图表类型、修改标题）。
    """
    return await report_service.update_report_service(db, report_id, body)

# -------------------------------------------
# 6. 导出报表 (Export)
# -------------------------------------------
@router.get("/reports/{report_id}/export", response_model=dict)
async def export_report(
    report_id: int,
    format: str = Query("png", regex="^(png|jpeg|pdf)$"),
    db: AsyncSession = Depends(get_db)
):
    return await report_service.export_report_service(db, report_id, format)