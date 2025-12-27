"""
项目 API 端点。

管理项目的全生命周期，包括创建（生成Schema、DDL、部署）、查询、更新和删除。
支持 Celery 异步任务状态查询。
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession as Session
from typing import Any, Optional, List

# 隐式绝对导入
from api.v1 import deps
from service import project_service
from schema import project as schemas
from schema.unified_response import UnifiedResponse, PageData
from core.exceptions import ItemNotFoundException, OperationNotPermittedException, ValidationException

router = APIRouter()


# =========================================================
# 任务状态查询接口
# =========================================================
@router.get("/tasks/{task_id}", response_model=UnifiedResponse[schemas.TaskStatusResponse])
async def get_task_status(
    task_id: str,
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    查询 Celery 异步任务状态。

    Args:
        task_id (str): Celery 任务 ID。
        current_user (Any): 当前登录用户。

    Returns:
        UnifiedResponse[schemas.TaskStatusResponse]: 任务状态响应。
    """
    result = await project_service.get_task_status_service(task_id)
    return UnifiedResponse.success(data=result, message="获取任务状态成功")


# 1. 创建项目 (第一步：只生成 Schema)
@router.post("/", response_model=UnifiedResponse[schemas.ProjectAsyncResponse])
async def create_project(
    project_in: schemas.ProjectCreate,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    创建项目第一步：
    1. 创建项目记录。
    2. 触发 Celery 后台任务生成 Logical Schema 和 ER 图。
    3. 返回项目ID和任务ID，用户可通过任务ID查询生成状态。

    Args:
        project_in (schemas.ProjectCreate): 项目创建请求体。
        db (Session): 数据库会话依赖。
        current_user (Any): 当前登录用户。

    Returns:
        UnifiedResponse[schemas.ProjectAsyncResponse]: 异步响应，包含项目ID和任务ID。
    """
    result = await project_service.create_project_service(db, project_in, current_user.user_id)
    return UnifiedResponse.success(data=result, message="项目创建请求已提交")


# =========================================================
# 接口：生成 DDL (第二步：用户确认 Schema 后调用)
# =========================================================
@router.post("/{project_id}/generate-ddl", response_model=UnifiedResponse[schemas.ProjectAsyncResponse])
async def generate_ddl(
    project_id: int,
    request_data: schemas.GenerateDDLRequest,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    创建项目第二步：
    1. 接收用户确认/修改后的 Schema。
    2. 触发 Celery 后台任务生成 DDL。
    3. 如果 Schema 有修改，同时重新生成 ER 图。

    Args:
        project_id (int): 项目ID。
        request_data (schemas.GenerateDDLRequest): 生成DDL请求体。
        db (Session): 数据库会话依赖。
        current_user (Any): 当前登录用户。

    Returns:
        UnifiedResponse[schemas.ProjectAsyncResponse]: 异步响应，包含项目ID和任务ID。
    """
    result = await project_service.request_ddl_generation_service(
        db, project_id, current_user.user_id, request_data
    )
    return UnifiedResponse.success(data=result, message="DDL生成请求已提交")

# =========================================================
# 执行部署 (第三步：用户确认 DDL 后调用)
# =========================================================
@router.post("/{project_id}/deploy", response_model=UnifiedResponse[schemas.ProjectDetailOut])
async def deploy_project(
    project_id: int,
    deploy_data: schemas.ProjectDeployRequest,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    创建项目第三步：
    1. 接收用户确认/修改后的 DDL。
    2. 执行建库建表。
    3. 项目状态变为 Active。

    Args:
        project_id (int): 项目ID。
        deploy_data (schemas.ProjectDeployRequest): 部署请求体。
        db (Session): 数据库会话依赖。
        current_user (Any): 当前登录用户。

    Returns:
        UnifiedResponse[schemas.ProjectDetailOut]: 部署后的项目信息。
    """
    result = await project_service.deploy_project_service(
        db, project_id, current_user.user_id, deploy_data
    )
    return UnifiedResponse.success(data=result, message="项目部署成功")


# 2. 获取列表 (分页)
@router.get("/", response_model=UnifiedResponse[PageData[List[schemas.ProjectListOne]]])
async def read_projects(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    分页获取项目列表。

    Args:
        search (Optional[str]): 搜索关键字。
        page (int): 页码。
        page_size (int): 每页数量。
        db (Session): 数据库会话依赖。
        current_user (Any): 当前登录用户。

    Returns:
        UnifiedResponse[PageData[List[schemas.ProjectListOne]]]: 分页项目列表响应。
    """
    result = await project_service.get_projects_list_service(db, current_user.user_id, search, page, page_size)
    page_data = PageData(
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        items=result.items
    )
    return UnifiedResponse.success(data=page_data, message="获取项目列表成功")

# 3. 获取详情
@router.get("/{project_id}", response_model=UnifiedResponse[schemas.ProjectDetailOut])
async def read_project_detail(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取项目详情。

    Args:
        project_id (int): 项目 ID。
        db (Session): 数据库会话依赖。
        current_user (Any): 当前登录用户。

    Returns:
        UnifiedResponse[schemas.ProjectDetailOut]: 项目详情响应。
    """
    result = await project_service.get_project_detail_service(db, project_id, current_user.user_id)
    return UnifiedResponse.success(data=result, message="获取项目详情成功")

# 4. 更新项目
@router.patch("/{project_id}", response_model=UnifiedResponse[schemas.ProjectDetailOut])
async def update_project_info(
    project_id: int,
    update_data: schemas.ProjectUpdate,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    更新项目信息。

    Args:
        project_id (int): 项目 ID。
        update_data (schemas.ProjectUpdate): 更新数据。
        db (Session): 数据库会话依赖。
        current_user (Any): 当前登录用户。

    Returns:
        UnifiedResponse[schemas.ProjectDetailOut]: 更新后的项目信息响应。
    """
    result = await project_service.update_project_info_service(db, project_id, current_user.user_id, update_data.model_dump(exclude_unset=True))
    return UnifiedResponse.success(data=result, message="项目信息更新成功")

# 5. 确认删除
@router.post("/{project_id}/confirm-delete", response_model=UnifiedResponse[schemas.ConfirmationTokenResponse])
async def confirm_delete(
    project_id: int,
    data: schemas.DeleteConfirmationRequest,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    确认删除项目，生成删除令牌。

    Args:
        project_id (int): 项目 ID。
        data (schemas.DeleteConfirmationRequest): 删除确认请求体。
        db (Session): 数据库会话依赖。
        current_user (Any): 当前登录用户。

    Returns:
        UnifiedResponse[schemas.ConfirmationTokenResponse]: 删除令牌响应。
    """
    result = await project_service.confirm_delete_project_service(db, project_id, current_user.user_id, data.confirmation_text)
    return UnifiedResponse.success(data=result, message="删除确认成功，令牌已生成")

# 6. 最终删除
@router.delete("/{project_id}", response_model=UnifiedResponse[None])
async def delete_project(
    project_id: int,
    x_confirmation_token: str = Header(..., alias="X-Confirmation-Token"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    最终删除项目。

    Args:
        project_id (int): 项目 ID。
        x_confirmation_token (str): 删除令牌。
        db (Session): 数据库会话依赖。
        current_user (Any): 当前登录用户。

    Returns:
        UnifiedResponse[None]: 删除成功响应。
    """
    await project_service.delete_project_service(db, project_id, current_user.user_id, x_confirmation_token)
    return UnifiedResponse.success(data=None, message="项目删除成功")


# =========================================================
# 重新生成 ER 图
# =========================================================
@router.post("/{project_id}/regenerate-er", response_model=UnifiedResponse[schemas.ProjectAsyncResponse])
async def regenerate_er_diagram(
    project_id: int,
    request_data: schemas.RegenerateERRequest,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    重新生成项目的 ER 图。

    当用户修改 Schema 后，可以调用此接口异步重新生成 ER 图。

    Args:
        project_id (int): 项目 ID。
        request_data (schemas.RegenerateERRequest): 重新生成 ER 图请求体。
        db (Session): 数据库会话依赖。
        current_user (Any): 当前登录用户。

    Returns:
        UnifiedResponse[schemas.ProjectAsyncResponse]: 异步响应，包含任务ID。
    """
    result = await project_service.regenerate_project_er_service(
        db, project_id, current_user.user_id,
        request_data.schema_text, request_data.ai_model
    )
    return UnifiedResponse.success(data=result, message="ER图重新生成请求已提交")
