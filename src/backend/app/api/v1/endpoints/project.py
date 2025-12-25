"""
项目 API 端点。

管理项目的全生命周期，包括创建（生成Schema、DDL、部署）、查询、更新和删除。
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header,BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession as Session
from typing import Any, Optional

# 隐式绝对导入
from api.v1 import deps
from service import project_service
from schema import project as schemas
from core.exceptions import ItemNotFoundException, OperationNotPermittedException, ValidationException

router = APIRouter()

# 1. 创建项目 (第一步：只生成 Schema)
@router.post("/", response_model=schemas.ProjectAsyncResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_project(
    project_in: schemas.ProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    创建项目第一步：
    1. 创建项目记录。
    2. 触发后台任务生成 Logical Schema。
    3. 返回项目ID，用户需轮询状态直到 schema_generated。

    Args:
        project_in (schemas.ProjectCreate): 项目创建请求体。
        background_tasks (BackgroundTasks): 后台任务对象。
        db (Session): 数据库会话依赖。
        current_user (Any): 当前登录用户。

    Returns:
        Any: 异步响应，包含项目ID。
    """
    return await project_service.create_project_service(db, project_in, current_user.user_id, background_tasks)

# =========================================================
# 新增接口：生成 DDL (第二步：用户确认 Schema 后调用)
# =========================================================
@router.post("/{project_id}/generate-ddl", response_model=schemas.ProjectAsyncResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_ddl(
    project_id: int,
    request_data: schemas.GenerateDDLRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    """
    创建项目第二步：
    1. 接收用户确认/修改后的 Schema。
    2. 触发后台任务生成 DDL。

    Args:
        project_id (int): 项目ID。
        request_data (schemas.GenerateDDLRequest): 生成DDL请求体。
        background_tasks (BackgroundTasks): 后台任务对象。
        db (Session): 数据库会话依赖。
        current_user (Any): 当前登录用户。

    Returns:
        Any: 异步响应，包含项目ID。
    """
    return await project_service.request_ddl_generation_service(
        db, project_id, current_user.user_id, request_data, background_tasks
    )

# =========================================================
# 执行部署 (第三步：用户确认 DDL 后调用)
# =========================================================
@router.post("/{project_id}/deploy", response_model=schemas.ProjectResponse)
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
        Any: 部署后的项目信息。
    """
    return await project_service.deploy_project_service(
        db, project_id, current_user.user_id, deploy_data
    )


# 2. 获取列表 (分页)
@router.get("/", response_model=schemas.PaginatedProjectList)
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
        Any: 分页项目列表响应。
    """
    return await project_service.get_projects_list_service(db, current_user.user_id, search, page, page_size)

# 3. 获取详情
@router.get("/{project_id}", response_model=schemas.ProjectResponse)
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
        Any: 项目详情响应。
    """
    return await project_service.get_project_detail_service(db, project_id, current_user.user_id)

# 4. 更新项目
@router.patch("/{project_id}", response_model=schemas.ProjectResponse)
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
        Any: 更新后的项目信息。
    """
    return await project_service.update_project_info_service(db, project_id, current_user.user_id, update_data.model_dump(exclude_unset=True))

# 5. 确认删除
@router.post("/{project_id}/confirm-delete", response_model=schemas.ConfirmationTokenResponse)
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
        Any: 删除令牌响应。
    """
    return await project_service.confirm_delete_project_service(db, project_id, current_user.user_id, data.confirmation_text)

# 6. 最终删除
@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    x_confirmation_token: str = Header(..., alias="X-Confirmation-Token"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
):
    """
    最终删除项目。

    Args:
        project_id (int): 项目 ID。
        x_confirmation_token (str): 删除令牌。
        db (Session): 数据库会话依赖。
        current_user (Any): 当前登录用户。

    Returns:
        None
    """
    await project_service.delete_project_service(db, project_id, current_user.user_id, x_confirmation_token)
    return None
