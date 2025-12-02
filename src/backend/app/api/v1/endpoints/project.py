# backend/app/api/v1/endpoints/project.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header,BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession as Session
from typing import Any, Optional

# 隐式绝对导入
from api.v1 import deps
from service import project_service
from schema import project as schemas
from core.exceptions import ItemNotFoundException, OperationNotPermittedException, ValidationException

router = APIRouter()

# 1. 创建项目 (202 Accepted)
@router.post("/", response_model=schemas.ProjectAsyncResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_project(
    project_in: schemas.ProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    try:
        return await project_service.create_project_service(db, project_in, current_user.user_id, background_tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. 获取列表 (分页)
@router.get("/", response_model=schemas.PaginatedProjectList)
async def read_projects(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    return await project_service.get_projects_list_service(db, current_user.user_id, search, page, page_size)

# 3. 获取详情
@router.get("/{project_id}", response_model=schemas.ProjectResponse)
async def read_project_detail(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    try:
        return await project_service.get_project_detail_service(db, project_id, current_user.user_id)
    except ItemNotFoundException:
        raise HTTPException(status_code=404, detail="Not found")

# 4. 更新项目
@router.patch("/{project_id}", response_model=schemas.ProjectResponse)
async def update_project_info(
    project_id: int,
    update_data: schemas.ProjectUpdate,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    try:
        return await project_service.update_project_info_service(db, project_id, current_user.user_id, update_data.model_dump(exclude_unset=True))
    except ItemNotFoundException:
        raise HTTPException(status_code=404, detail="Not found")

# 5. 确认删除
@router.post("/{project_id}/confirm-delete", response_model=schemas.ConfirmationTokenResponse)
async def confirm_delete(
    project_id: int,
    data: schemas.DeleteConfirmationRequest,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    try:
        return await project_service.confirm_delete_project_service(db, project_id, current_user.user_id, data.confirmation_text)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))

# 6. 最终删除
@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    x_confirmation_token: str = Header(..., alias="X-Confirmation-Token"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
):
    try:
        await project_service.delete_project_service(db, project_id, current_user.user_id, x_confirmation_token)
        return None
    except OperationNotPermittedException as e:
        raise HTTPException(status_code=403, detail=str(e))