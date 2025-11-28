# backend/app/api/v1/endpoints/project.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession as Session
from typing import Any, Optional, Dict, List
from pydantic import BaseModel, ConfigDict  # 引入 BaseModel 用于定义新的响应 Schema

# 隐式绝对导入
from api.v1 import deps
from service import project_service  # <-- 假设此文件包含所有 Project/Query Service 函数
from schema import project as schemas  # 导入 Project Schemas
from core.exceptions import ItemNotFoundException, DatabaseOperationFailedException, OperationNotPermittedException, \
    ValidationException

router = APIRouter()


# ----------------------------------------------------------------------
# 辅助 Schema：查询结果的响应模型 (根据 Service 层返回结构定义)
# ----------------------------------------------------------------------
class QueryResultResponse(BaseModel):
    """
    Service 层 get_report_data_by_id_service 函数的返回结构。
    """
    result_data: Any  # 实际的 JSON/数据结果 (如表格数据、图表数据等)
    data_summary: Optional[str] = None
    chart_type: Optional[str] = None
    sql_text: Optional[str] = None
    cached_at: Optional[str] = None  # ISO 8601 格式的缓存时间


# ----------------------------------------------------------------------
# 新增接口: GET /projects/query-result/{query_id} - 获取查询结果 JSON
# 对应逻辑：前端给 query_id -> Router -> Service -> CRUD (query_result表) -> JSON 返回
# ----------------------------------------------------------------------
@router.get("/query-result/{query_id}", response_model=QueryResultResponse)
async def get_query_json_result(
        query_id: int,
        db: Session = Depends(deps.get_db),
        current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    根据 Query ID (即 result_id) 获取存储在数据库中的 JSON 查询结果。
    此接口将 Query ID 转发至 Service 层，Service 层负责调用 CRUD 查询结果表。
    """
    try:
        # 1. 调用 Service 层函数 (使用你提供的 service 层函数名)
        result_data_dict = await project_service.get_report_data_by_id_service(
            db,
            query_id
        )

        # 2. 返回结果。FastAPI/Pydantic 会自动验证和序列化。
        return result_data_dict

    except ItemNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query result with ID {query_id} not found."
        )
    except DatabaseOperationFailedException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching query result: {e}"
        )
    except Exception as e:
        # 捕获其他非预期错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )


# ======================================================================
# 以下为前一次提供的项目管理接口（保留完整性）
# ======================================================================

# ----------------------------------------------------------------------
# 1. POST /projects - 创建项目 (对应前端 3.2.1 - 异步创建)
# ----------------------------------------------------------------------
# 假设 ProjectAsyncResponse DTO 已在 schema/project.py 中定义
@router.post("/", response_model=schemas.ProjectAsyncResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_project(
        project_in: schemas.ProjectCreate,
        db: Session = Depends(deps.get_db),
        current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    创建项目 (异步受理)，返回 202 Accepted。
    """
    try:
        response_dto = await project_service.create_project_service(
            db,
            project_in,
            user_id=current_user.user_id
        )
        return response_dto

    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"项目创建请求失败: {e}"
        )


# ----------------------------------------------------------------------
# 2. GET /projects - 获取项目列表 (对应前端 3.2.3 - 分页)
# ----------------------------------------------------------------------
# 假设 PaginatedProjectList DTO 已在 schema/project.py 中定义
@router.get("/", response_model=schemas.PaginatedProjectList)
async def read_projects(
        search: Optional[str] = Query(None, description="搜索项目名"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        db: Session = Depends(deps.get_db),
        current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取当前用户的所有项目 (包含分页和搜索)
    """
    try:
        paginated_list = await project_service.get_projects_list_service(
            db,
            user_id=current_user.user_id,
            search=search,
            page=page,
            page_size=page_size
        )
        return paginated_list

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取列表失败: {e}")


# ----------------------------------------------------------------------
# 3. GET /projects/{project_id} - 获取项目详情 (对应前端 3.2.2)
# ----------------------------------------------------------------------
# 假设 ProjectDetailResponse DTO 已在 schema/project.py 中定义
@router.get("/{project_id}", response_model=schemas.ProjectResponse)
async def read_project_detail(
        project_id: int,
        db: Session = Depends(deps.get_db),
        current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取项目详情 (含创建进度)
    """
    try:
        project_dto = await project_service.get_project_detail_service(
            db,
            project_id,
            current_user.user_id
        )
        return project_dto
    except ItemNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取详情失败: {e}")
    pass
# ----------------------------------------------------------------------
# 4. PATCH /projects/{project_id} - 更新项目信息 (对应前端 3.2.4)
# ----------------------------------------------------------------------
# 假设 ProjectUpdate DTO 已在 schema/project.py 中定义
@router.patch("/{project_id}", response_model=schemas.ProjectResponse)
async def update_project_info(
        project_id: int,
        update_data: schemas.ProjectUpdate,
        db: Session = Depends(deps.get_db),
        current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    更新项目基本信息 (名称、描述等)
    """
    try:
        updated_dto = await project_service.update_project_info_service(
            db,
            project_id,
            current_user.user_id,
            update_data.model_dump(exclude_unset=True)
        )
        return updated_dto
    except ItemNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    except OperationNotPermittedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    pass

# ----------------------------------------------------------------------
# 5. POST /projects/{project_id}/confirm-delete - 确认删除 (对应前端 3.2.5)
# ----------------------------------------------------------------------
# 假设 DeleteConfirmationRequest 和 ConfirmationTokenResponse DTO 已定义
@router.post("/{project_id}/confirm-delete", response_model=schemas.ConfirmationTokenResponse)
async def confirm_delete_project(
        project_id: int,
        data: schemas.DeleteConfirmationRequest,
        db: Session = Depends(deps.get_db),
        current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    请求删除确认令牌 (软删除的第一步)
    """
    try:
        return await project_service.confirm_delete_project_service(
            db, project_id, current_user.user_id, data.confirmation_text
        )
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Deletion confirmation failed: {e}")


# ----------------------------------------------------------------------
# 6. DELETE /projects/{project_id} - 最终删除 (对应前端 3.2.5)
# ----------------------------------------------------------------------
@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
        project_id: int,
        x_confirmation_token: str = Header(..., alias="X-Confirmation-Token"),
        db: Session = Depends(deps.get_db),
        current_user: Any = Depends(deps.get_current_active_user),
):
    """
    执行项目删除 (软删除)
    """
    try:
        success = await project_service.delete_project_service(
            db, project_id, current_user.user_id, x_confirmation_token
        )

        if not success:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Invalid confirmation token or project not found.")

        return None
    except OperationNotPermittedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Deletion failed: {e}")