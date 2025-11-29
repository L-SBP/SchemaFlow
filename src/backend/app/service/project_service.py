# backend/app/service/project_service.py

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession as Session
from datetime import datetime, timedelta, timezone

# 隐式绝对导入
from crud.crud_project import crud_project
# 引入 DatabaseInstance CRUD 以解决外键问题
from crud.crud_database_instance import crud_database_instance
from schema import project as schemas
from core.exceptions import ItemNotFoundException, DatabaseOperationFailedException, OperationNotPermittedException, \
    ValidationException
from core.auth import decode_jwt_token, create_access_token
from core.config import config


# 假设 Tasks 模块
# from tasks import project_creation_task

# --- 辅助函数 ---
async def _verify_delete_token(token: str, user_id: int, project_id: int) -> bool:
    try:
        payload = decode_jwt_token(token)
        if payload.get("sub") != str(user_id) or payload.get("project_id") != project_id:
            return False
        return True
    except Exception:
        return False


# --- 1. 创建项目 ---
async def create_project_service(
        db: Session, project_in: schemas.ProjectCreate, user_id: int
) -> schemas.ProjectAsyncResponse:
    """创建项目：先创建 DB 实例，再创建项目记录，最后调度异步任务"""
    try:
        project_data = project_in.model_dump()
        db_type = project_data.pop('db_type')

        # 1. 创建关联的 DatabaseInstance (占位)
        # 必须先创建它，否则 Project 的 instance_id 外键会报错
        new_instance = await crud_database_instance.create(
            db,
            db_type=db_type,
            db_host="", db_port=0, db_name="pending", db_username="", db_password="",
            status="inactive"
        )

        # 2. 创建 Project
        project_data['user_id'] = user_id
        project_data['instance_id'] = new_instance.instance_id
        project_data['project_status'] = 'initializing'

        db_obj = await crud_project.create(db, **project_data)

        # 3. 调度异步任务 (此处解开注释即可工作)
        # project_creation_task.delay(project_id=db_obj.project_id)

        return schemas.ProjectAsyncResponse.model_validate(db_obj)
    except Exception as e:
        raise DatabaseOperationFailedException(f"Create failed: {e}")


# --- 2. 获取列表 ---
async def get_projects_list_service(
        db: Session, user_id: int, search: Optional[str], page: int, page_size: int
) -> schemas.PaginatedProjectList:
    skip = (page - 1) * page_size
    total = await crud_project.get_total_count_by_user(db, user_id, search)
    items = await crud_project.get_by_user(db, user_id, skip, page_size, search)

    return schemas.PaginatedProjectList(
        total=total, page=page, page_size=page_size,
        items=[schemas.ProjectListOne.model_validate(i) for i in items]
    )


# ----------------------------------------------------------------------
# 3. GET Project Detail
# ----------------------------------------------------------------------
async def get_project_detail_service(
        db: Session,
        project_id: int,
        user_id: int
) -> schemas.ProjectResponse:  # <--- 修正点 1：这里原来是 ProjectDetailResponse
    """
    Service: 获取项目详情，并检查用户权限。
    """
    db_obj = await crud_project.get(db, project_id)

    if not db_obj or db_obj.user_id != user_id:
        raise ItemNotFoundException("Project not found or access denied.")

    # <--- 修正点 2：使用 ProjectResponse 包装
    return schemas.ProjectResponse(data=schemas.ProjectDetailOut.model_validate(db_obj))


# ----------------------------------------------------------------------
# 4. PATCH Update Project
# ----------------------------------------------------------------------
async def update_project_info_service(
        db: Session,
        project_id: int,
        user_id: int,
        update_data: Dict[str, Any]
) -> schemas.ProjectResponse:  # <--- 修正点 3：这里原来是 ProjectDetailResponse
    """
    Service: 更新项目信息，检查权限和状态。
    """
    db_obj = await crud_project.get(db, project_id)

    if not db_obj or db_obj.user_id != user_id:
        raise ItemNotFoundException("Project not found or access denied.")

    if db_obj.project_status == 'deleted':
        raise OperationNotPermittedException("Cannot update a deleted project.")

    updated_obj = await crud_project.update(db, project_id, **update_data)

    # <--- 修正点 4：使用 ProjectResponse 包装
    return schemas.ProjectResponse(data=schemas.ProjectDetailOut.model_validate(updated_obj))


# --- 5. 确认删除 (生成Token) ---
async def confirm_delete_project_service(
        db: Session, project_id: int, user_id: int, confirmation_text: str
) -> schemas.ConfirmationTokenResponse:
    if confirmation_text != "DELETE":
        raise ValidationException("Confirmation text must be 'DELETE'.")

    # 检查权限
    db_obj = await crud_project.get(db, project_id)
    if not db_obj or db_obj.user_id != user_id:
        raise ItemNotFoundException("Project not found.")

    # 生成 Token
    payload = {"sub": str(user_id), "project_id": project_id}
    token = create_access_token(payload)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=config.jwt.token_expire_time_seconds)

    return schemas.ConfirmationTokenResponse(confirmation_token=token, expires_at=expires_at)


# --- 6. 最终删除 ---
async def delete_project_service(
        db: Session, project_id: int, user_id: int, confirmation_token: str
) -> bool:
    if not await _verify_delete_token(confirmation_token, user_id, project_id):
        raise OperationNotPermittedException("Invalid token.")

    # 执行软删除
    await crud_project.change_status(db, project_id, 'deleted')
    return True