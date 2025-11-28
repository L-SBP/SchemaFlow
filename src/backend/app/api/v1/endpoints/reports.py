# backend/app/api/v1/endpoints/reports.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession as Session
from typing import List, Dict, Any

# 隐式绝对导入
from api.v1.deps import get_db, get_current_active_user
from schema import report as schemas
from service import report_service

router = APIRouter()

# 4.1 获取报表列表
@router.get("/reports", response_model=List[schemas.Report])
async def read_reports(
    projectId: str = Query(..., description="项目ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """获取报表列表 (Reports GET)"""
    # Router 严格只调用 Service，返回数组
    return await report_service.get_report_list(db, projectId)

# 4.4 获取历史查询记录
@router.get("/history-queries", response_model=List[schemas.HistoryQuery])
async def read_history(
    projectId: str = Query(..., description="项目ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """获取历史查询记录 (History Queries GET)"""
    # 假设 service 提供了 get_history_queries 函数
    # return await report_service.get_history_queries(db, projectId)
    return []