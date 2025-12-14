"""
报表 API 端点。

提供报表的增删改查、导出及历史查询记录获取功能。
"""
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from schema.report import ReportCreate, Report, HistoryQuery, ReportUpdate
from schema.user import UserMe
from api.v1.deps import get_db, get_current_active_user
from service import report_service

router = APIRouter()

# -------------------------------------------
# 1. 获取报表列表 (Read)
# -------------------------------------------
@router.get("/reports", response_model=List[Report], summary="获取报表列表")
async def read_reports(
    projectId: int = Query(..., description="项目ID"),
    db: AsyncSession = Depends(get_db),
    user: UserMe = Depends(get_current_active_user),
):
    """
    获取指定项目下的所有保存的报表配置（仅限当前用户的项目）。

    Args:
        projectId (int): 项目ID。
        db (AsyncSession): 数据库会话。
        user (UserMe): 当前登录用户。

    Returns:
        List[Report]: 报表列表。
    """
    return await report_service.get_report_list(
        db=db,
        project_id=projectId,
        user_id=user.user_id
    )


# -------------------------------------------
# 2. 获取历史查询记录
# -------------------------------------------
@router.get("/history-queries", response_model=List[HistoryQuery], summary="获取历史查询记录")
async def read_history(
    projectId: int = Query(..., description="项目ID"),
    db: AsyncSession = Depends(get_db),
    user: UserMe = Depends(get_current_active_user),
):
    """
    获取历史查询结果，用于作为创建新报表的数据源（仅限当前用户的项目）。

    Args:
        projectId (int): 项目ID。
        db (AsyncSession): 数据库会话。
        user (UserMe): 当前登录用户。

    Returns:
        List[HistoryQuery]: 历史查询记录列表。
    """
    return await report_service.get_history_queries_service(
        db=db,
        project_id=projectId,
        user_id=user.user_id
    )


# -------------------------------------------
# 3. 创建报表 (Create)
# -------------------------------------------
@router.post(
    "/projects/{project_id}/reports",
    response_model=Report,
    summary="创建报表"
)
async def create_report(
    body: ReportCreate,
    project_id: int = Path(..., description="项目ID"),
    db: AsyncSession = Depends(get_db),
    user: UserMe = Depends(get_current_active_user),
):
    """
    在指定项目下创建报表（仅限当前用户的项目）。

    Args:
        body (ReportCreate): 报表创建请求体。
        project_id (int): 项目ID。
        db (AsyncSession): 数据库会话。
        user (UserMe): 当前登录用户。

    Returns:
        Report: 创建后的报表信息。
    """
    return await report_service.create_report_service(
        db=db,
        project_id=project_id,
        payload=body,
        user_id=user.user_id
    )


# -------------------------------------------
# 4. 删除报表 (Delete)
# -------------------------------------------
@router.delete(
    "/reports/{report_id}",
    response_model=bool,
    summary="删除报表"
)
async def delete_report(
    report_id: int = Path(..., description="报表ID"),
    db: AsyncSession = Depends(get_db),
    user: UserMe = Depends(get_current_active_user),
):
    """
    删除指定报表（仅限当前用户）。

    Args:
        report_id (int): 报表ID。
        db (AsyncSession): 数据库会话。
        user (UserMe): 当前登录用户。

    Returns:
        bool: 删除成功返回True。
    """
    return await report_service.delete_report_service(
        db=db,
        report_id=report_id,
        user_id=user.user_id
    )


# -------------------------------------------
# 5. 修改报表信息 (Update)
# -------------------------------------------
@router.put(
    "/reports/{report_id}",
    response_model=Report,
    summary="更新报表"
)
async def update_report(
    body: ReportUpdate,
    report_id: int = Path(..., description="报表ID"),
    db: AsyncSession = Depends(get_db),
    user: UserMe = Depends(get_current_active_user),
):
    """
    修改报表配置（仅限当前用户）。

    Args:
        body (ReportUpdate): 报表更新请求体。
        report_id (int): 报表ID。
        db (AsyncSession): 数据库会话。
        user (UserMe): 当前登录用户。

    Returns:
        Report: 更新后的报表信息。
    """
    return await report_service.update_report_service(
        db=db,
        report_id=report_id,
        payload=body,
        user_id=user.user_id
    )


# -------------------------------------------
# 6. 导出报表 (Export)
# -------------------------------------------
@router.get(
    "/reports/{report_id}/export",
    response_model=dict,
    summary="导出报表"
)
async def export_report(
    report_id: int = Path(..., description="报表ID"),
    format: str = Query("png", regex="^(png|jpeg|pdf)$"),
    db: AsyncSession = Depends(get_db),
    user: UserMe = Depends(get_current_active_user),
):
    """
    导出报表（仅限当前用户）。

    Args:
        report_id (int): 报表ID。
        format (str): 导出格式(png, jpeg, pdf)。
        db (AsyncSession): 数据库会话。
        user (UserMe): 当前登录用户。

    Returns:
        dict: 包含导出文件信息的字典。
    """
    return await report_service.export_report_service(
        db=db,
        report_id=report_id,
        format=format,
        user_id=user.user_id
    )
