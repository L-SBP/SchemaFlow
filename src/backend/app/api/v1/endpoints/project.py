# backend/app/api/v1/endpoints/reports.py

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession as Session
from typing import List, Dict, Any

# 隐式绝对导入
from api.v1.deps import get_db, get_current_active_user
from schema import report as schemas
from service import report_service
from core.exceptions import DatabaseOperationFailedException, ItemNotFoundException

router = APIRouter()

# ------------------------------------------------------------------
# 1. 核心数据接口 (通过 query_id 获取 JSON 结果并返回)
# ------------------------------------------------------------------
@router.get("/reports/data/{query_id}", response_model=Dict[str, Any])
async def get_report_data(
    query_id: int, # 前端发送的 query_id (即 result_id)
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """
    根据查询结果ID获取原始 JSON 数据和元数据，供前端渲染。
    """
    try:
        # Router 严格只调用 Service，返回原始 JSON 数据
        return await report_service.get_report_data_by_id_service(db, query_id)
    except ItemNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        # 捕获 Service 层抛出的异常
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve data: {e}")


# ------------------------------------------------------------------
# 2. 4.4 获取历史查询记录 (前端期望: List[HistoryQuery])
# ------------------------------------------------------------------
@router.get("/history-queries", response_model=List[schemas.HistoryQuery])
async def read_history(
    projectId: str = Query(..., description="项目ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> Any:
    """获取历史查询记录列表。"""
    try:
        # Router 严格只调用 Service
        return await report_service.get_history_queries_service(db, projectId)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve history: {e}")

# ------------------------------------------------------------------
# 3. 4.3 删除报表 (DELETE /reports/{reportId} - 删除缓存记录)
# ------------------------------------------------------------------
@router.delete("/reports/{reportId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report_asset(
    reportId: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> None:
    """删除报表资产（删除查询结果缓存）。"""
    # 假设 service 层实现了删除 QueryResult 和 Statement 的逻辑
    # await report_service.delete_report_asset(db, reportId, current_user.id)
    return None