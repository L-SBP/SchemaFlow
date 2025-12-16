"""
知识库/术语 API 端点。

管理项目的业务术语，包括增删改查、批量导入导出等操作。
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Path
from sqlalchemy.ext.asyncio import AsyncSession as Session
from typing import Any, Optional

# 隐式绝对导入
from api.v1 import deps
from service import knowledge_service
from schema import knowledge as schemas
from core.exceptions import ItemNotFoundException, ValidationException

# 注意：这个 Router 稍后需要在 api.py 中注册，且不带 prefix，因为路径包含 {project_id}
router = APIRouter()

# ----------------------------------------------------------------------
# 3.4.1. 创建术语
# ----------------------------------------------------------------------
@router.post("/projects/{project_id}/knowledge", response_model=schemas.KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def create_term(
    data: schemas.KnowledgeCreate,
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    创建新业务术语。

    Args:
        data (schemas.KnowledgeCreate): 术语创建请求体。
        project_id (int): 项目 ID。
        db (Session): 数据库会话。
        current_user (Any): 当前登录用户。

    Returns:
        Any: 创建后的术语信息。

    Raises:
        HTTPException: 项目未找到(404)、冲突(409)或内部错误(500)。
    """
    try:
        return await knowledge_service.create_knowledge_service(db, project_id, current_user.user_id, data)
    except ItemNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) # 409 for conflict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------
# 3.4.2. 获取术语列表
# ----------------------------------------------------------------------
@router.get("/projects/{project_id}/knowledge", response_model=schemas.PaginatedKnowledgeList)
async def get_terms(
    project_id: int = Path(..., description="项目ID"),
    search: Optional[str] = Query(None, description="按术语名称搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取项目中的所有术语。

    Args:
        project_id (int): 项目 ID。
        search (Optional[str]): 搜索关键字。
        page (int): 页码。
        page_size (int): 每页数量。
        db (Session): 数据库会话。
        current_user (Any): 当前登录用户。

    Returns:
        Any: 分页术语列表。

    Raises:
        HTTPException: 项目未找到(404)或内部错误(500)。
    """
    try:
        return await knowledge_service.get_knowledge_list_service(
            db, project_id, current_user.user_id, page, page_size, search
        )
    except ItemNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------
# [新增] 更新术语
# ----------------------------------------------------------------------
@router.patch("/projects/{project_id}/knowledge/{knowledge_id}", response_model=schemas.KnowledgeResponse)
async def update_term(
    data: schemas.KnowledgeUpdate,
    project_id: int = Path(..., description="项目ID"),
    knowledge_id: int = Path(..., description="术语ID"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    更新术语信息。

    Args:
        data (schemas.KnowledgeUpdate): 术语更新请求体。
        project_id (int): 项目 ID。
        knowledge_id (int): 术语 ID。
        db (Session): 数据库会话。
        current_user (Any): 当前登录用户。

    Returns:
        Any: 更新后的术语信息。

    Raises:
        HTTPException: 术语/项目未找到(404)或内部错误(500)。
    """
    try:
        return await knowledge_service.update_knowledge_service(
            db, project_id, knowledge_id, current_user.user_id, data
        )
    except ItemNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term or Project not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------
# [新增] 批量删除术语
# ----------------------------------------------------------------------
@router.delete("/projects/{project_id}/knowledge/batch", response_model=schemas.ImportResponse) # 复用 ImportResponse 或新建一个 DeleteResponse
async def batch_delete_terms(
    data: schemas.BulkDeleteRequest,
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    批量删除术语。

    Args:
        data (schemas.BulkDeleteRequest): 批量删除请求体。
        project_id (int): 项目 ID。
        db (Session): 数据库会话。
        current_user (Any): 当前登录用户。

    Returns:
        Any: 删除结果。

    Raises:
        HTTPException: 项目未找到(404)或内部错误(500)。
    """
    try:
        count = await knowledge_service.batch_delete_knowledge_service(
            db, project_id, current_user.user_id, data.ids
        )
        # 这里临时构造一个返回，您也可以定义专门的 DeleteResponse
        return {"imported_count": 0, "failed_count": 0, "failures": [], "message": f"Successfully deleted {count} items."}
    except ItemNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ----------------------------------------------------------------------
# 3.4.3. 批量导入术语
# ----------------------------------------------------------------------
@router.post("/projects/{project_id}/knowledge/import", response_model=schemas.ImportResponse)
async def import_terms(
    project_id: int = Path(..., description="项目ID"),
    file: UploadFile = File(..., description="CSV 文件"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    从文件批量导入术语。

    Args:
        project_id (int): 项目 ID。
        file (UploadFile): 上传的文件。
        db (Session): 数据库会话。
        current_user (Any): 当前登录用户。

    Returns:
        Any: 导入结果统计。

    Raises:
        HTTPException: 格式错误(400)、项目未找到(404)或导入失败(500)。
    """
    try:
        return await knowledge_service.import_knowledge_service(
            db, project_id, current_user.user_id, file
        )
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ItemNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {e}")


# ----------------------------------------------------------------------
# 3.4.4. 导出术语
# ----------------------------------------------------------------------
@router.get("/projects/{project_id}/knowledge/export", response_model=schemas.ExportResponse)
async def export_terms(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    导出术语库。

    Args:
        project_id (int): 项目 ID。
        db (Session): 数据库会话。
        current_user (Any): 当前登录用户。

    Returns:
        Any: 导出文件下载链接。

    Raises:
        HTTPException: 项目未找到(404)或内部错误(500)。
    """
    try:
        return await knowledge_service.export_knowledge_service(db, project_id, current_user.user_id)
    except ItemNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))