"""
项目服务。

负责项目生命周期：生成 Schema、生成 DDL、部署、元数据更新、列表与详情、删除
等；集成 AI 生成器、数据库助手与 CRUD 层。

重构说明：
1. 将 generate_meaningful_db_name 移至 core/utils.py
2. 将配额校验逻辑独立为 _check_user_quota
3. 拆分臃肿的函数，每个函数控制在 50 行以内
4. 确保 AI 调用在事务外执行
"""

# backend/app/service/project_service.py

import asyncio
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession as Session
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import BackgroundTasks

from crud.crud_project import crud_project
from crud.crud_database_instance import crud_database_instance
from crud.crud_user_account import crud_user_account
from schema import project as schemas
from core.exceptions import (
    ItemNotFoundException,
    OperationNotPermittedException,
    ValidationException,
    InvalidOperationException
)
from core.auth import create_access_token
from core.config import config
from core.database import PsqlHelper
from core.log import log
from core.utils import generate_meaningful_db_name

from service.ai_service import AIService
from service.db_executor_service import DBExecutorService
from service.rag_service import rag_service

# Celery 任务导入
from tasks.ai_generation_tasks import (
    schema_er_pipeline_task,
    ddl_er_parallel_task,
    generate_er_task,
    get_task_status,
)

# 缓存相关
from redis_client.redis_keys import redis_key_manager
from redis_client.cache_service import cache_service


# =========================================================
# 缓存清除辅助函数
# =========================================================

async def _invalidate_project_cache(project_id: int, user_id: int = None) -> None:
    """
    清除项目相关的所有缓存。
    
    Args:
        project_id: 项目 ID
        user_id: 用户 ID
    """
    try:
        # 1. 清除项目详情缓存
        project_info_key = redis_key_manager.get_project_info_key(project_id)
        log.info(f"[Cache] Attempting to delete cache key: {project_info_key}")
        cache_deleted = await cache_service.delete(project_info_key)
        log.info(f"[Cache] Delete operation result for project info cache {project_info_key}: {cache_deleted}")
        
        # 2. 如果有 user_id，清除该用户的所有项目列表缓存
        if user_id:
            project_list_pattern = redis_key_manager.generate_key(
                redis_key_manager.USER_PREFIX, "projects", str(user_id), "*"
            )
            log.info(f"[Cache] Attempting to delete cache pattern: {project_list_pattern}")
            pattern_deleted_count = await cache_service.delete_pattern(project_list_pattern)
            log.info(f"[Cache] Delete pattern operation result for user {user_id} pattern {project_list_pattern}: {pattern_deleted_count} keys deleted")
            
            # 3. 清除用户信息缓存（包含 used_databases 项目计数）
            user_info_key = redis_key_manager.get_user_info_key(user_id)
            log.info(f"[Cache] Attempting to delete user info cache key: {user_info_key}")
            user_cache_deleted = await cache_service.delete(user_info_key)
            log.info(f"[Cache] Delete operation result for user info cache {user_info_key}: {user_cache_deleted}")
        
        log.info(f"[Cache] Completed cache invalidation for project {project_id}, user {user_id}")
    except Exception as e:
        log.error(f"[Cache] Exception occurred during cache invalidation for project {project_id}: {e}")
        log.warning(f"[Cache] Failed to invalidate cache for project {project_id}: {e}")


# =========================================================
# 配额与权限校验
# =========================================================

async def _check_user_quota(db: Session, user_id: int) -> Any:
    """
    检查用户配额是否充足。
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        
    Returns:
        用户对象
        
    Raises:
        ItemNotFoundException: 用户不存在
        OperationNotPermittedException: 配额已用尽
    """
    user = await crud_user_account.get(db, user_id)
    if not user:
        raise ItemNotFoundException("用户未找到")
    if user.used_databases >= user.max_databases:
        raise OperationNotPermittedException("配额已超出")
    return user


async def _verify_project_ownership(db: Session, project_id: int, user_id: int) -> Any:
    """
    验证项目所有权。
    
    Args:
        db: 数据库会话
        project_id: 项目 ID
        user_id: 用户 ID
        
    Returns:
        项目对象
        
    Raises:
        ItemNotFoundException: 项目不存在或无权限
    """
    project = await crud_project.get(db, project_id)
    if not project or project.user_id != user_id:
        raise ItemNotFoundException("项目未找到或访问被拒绝")
    return project


# =========================================================
# 数据库实例配置
# =========================================================

def _get_db_host_port(db_type: str) -> tuple:
    """
    根据数据库类型获取对应的 host 和 port。
    
    Args:
        db_type: 数据库类型
        
    Returns:
        (host, port) 元组
    """
    if db_type == 'mysql':
        return config.mysql.host, config.mysql.port
    elif db_type == 'postgresql':
        return config.postgresql.host, config.postgresql.port
    return "127.0.0.1", 3306


# =========================================================
# Celery 任务调度辅助函数
# =========================================================

def _dispatch_schema_er_task(
    project_id: int,
    requirements: str,
    db_name: str,
    db_type: str,
    ai_model: str
) -> str:
    """
    调度 Schema + ER 生成任务。
    
    Returns:
        task_id: Celery 任务 ID
    """
    task = schema_er_pipeline_task.delay(
        project_id=project_id,
        requirements=requirements,
        db_name=db_name,
        db_type=db_type,
        ai_model=ai_model
    )
    log.info(f"[Celery] Dispatched schema_er_pipeline_task for Project {project_id}, task_id={task.id}")
    return task.id


def _dispatch_ddl_er_task(
    project_id: int,
    schema_text: str,
    requirements: str,
    db_type: str,
    db_name: str,
    ai_model: str = "gpt4",
    regenerate_er: bool = True
) -> str:
    """
    调度 DDL + ER 并行生成任务。

    Returns:
        task_id: Celery 任务 ID
    """
    task = ddl_er_parallel_task.delay(
        project_id=project_id,
        schema_text=schema_text,
        requirements=requirements,
        db_type=db_type,
        db_name=db_name,
        ai_model=ai_model,
        regenerate_er=regenerate_er
    )
    log.info(f"[Celery] Dispatched ddl_er_parallel_task for Project {project_id}, task_id={task.id}")
    return task.id


def _dispatch_er_only_task(
    project_id: int,
    schema_text: str,
    ai_model: str = "gpt4"
) -> str:
    """
    调度仅 ER 图生成任务。

    Returns:
        task_id: Celery 任务 ID
    """
    task = generate_er_task.delay(
        project_id=project_id,
        schema_text=schema_text,
        ai_model=ai_model
    )
    log.info(f"[Celery] Dispatched generate_er_task for Project {project_id}, task_id={task.id}")
    return task.id


# =========================================================
# 创建项目服务
# =========================================================

async def _create_database_instance(
    db: Session,
    db_type: str,
    db_name: str,
    user_id: int
) -> Any:
    """创建数据库实例占位记录。"""
    target_host, target_port = _get_db_host_port(db_type)
    
    return await crud_database_instance.create(
        db,
        db_type=db_type,
        db_host=target_host,
        db_port=target_port,
        db_name=db_name,
        db_username=f"test_{user_id}",
        db_password="User_secure_2025",
        status="inactive"
    )


async def _create_project_record(
    db: Session,
    project_data: dict,
    user_id: int,
    instance_id: int
) -> Any:
    """创建项目记录。"""
    project_data['user_id'] = user_id
    project_data['instance_id'] = instance_id
    project_data['project_status'] = 'initializing'
    project_data['creation_stage'] = schemas.CreationStageEnum.GENERATING_SCHEMA.value
    
    return await crud_project.create(db, **project_data)


async def create_project_service(
    db: Session,
    project_in: schemas.ProjectCreate,
    user_id: int,
    background_tasks: BackgroundTasks = None  # 保留参数以兼容旧接口
) -> schemas.ProjectAsyncResponse:
    """
    创建项目并异步生成 Schema/ER 图。

    流程：
    1. 检查用户配额
    2. 创建项目记录
    3. 调度 Celery 任务生成 Schema + ER 图
    4. 返回项目信息和任务 ID
    """
    # 1. 检查用户配额
    user = await _check_user_quota(db, user_id)

    # 2. 解析请求参数
    project_data = project_in.model_dump()
    db_type = project_data.pop('db_type')
    ai_model = project_data.pop('ai_model', 'gpt4')
    requirements_text = project_data.get('description', '')
    project_name = project_data.get('project_name', 'project')

    # 3. 生成数据库名称
    temp_db_name = generate_meaningful_db_name(project_name, user_id)

    # 4. 创建数据库实例占位
    new_instance = await _create_database_instance(db, db_type, temp_db_name, user_id)

    # 5. 创建项目记录
    db_obj = await _create_project_record(db, project_data, user_id, new_instance.instance_id)

    # 6. 调度 Celery 任务：Schema + ER 生成流水线
    task_id = _dispatch_schema_er_task(
        project_id=db_obj.project_id,
        requirements=requirements_text,
        db_name=temp_db_name,
        db_type=db_type,
        ai_model=ai_model
    )

    # 7. 更新用户配额
    await crud_user_account.update(db, user, used_databases=user.used_databases + 1)

    # 8. 清除项目列表缓存，确保前端立即看到新项目
    await _invalidate_project_cache(db_obj.project_id, user_id)

    # 9. 返回项目信息（包含 task_id 供前端查询状态）
    response = schemas.ProjectAsyncResponse.model_validate(db_obj)
    response.task_id = task_id
    response.message = "项目创建成功，正在生成 Schema..."
    return response


# =========================================================
# DDL 生成请求服务
# =========================================================

async def request_ddl_generation_service(
    db: Session,
    project_id: int,
    user_id: int,
    data: schemas.GenerateDDLRequest,
    background_tasks: BackgroundTasks = None  # 保留参数以兼容旧接口
) -> schemas.ProjectAsyncResponse:
    """
    用户确认 Schema，后端触发 DDL 生成任务。

    流程：
    1. 保存用户确认/修改的 Schema
    2. 调度 Celery 任务生成 DDL
    3. 如果 Schema 有修改，同时重新生成 ER 图
    """
    project = await _verify_project_ownership(db, project_id, user_id)

    # 检查 Schema 是否有变化（用于决定是否重新生成 ER 图）
    old_schema = (project.schema_definition or {}).get('schema', '')
    new_schema = data.confirmed_schema
    schema_changed = old_schema != new_schema

    # 更新需求描述（如果有）
    if data.requirements:
        project.description = data.requirements

    # 更新 Schema - 创建新字典以确保 SQLAlchemy 检测到变化
    from sqlalchemy.orm.attributes import flag_modified
    current_def = dict(project.schema_definition or {})
    current_def['schema'] = new_schema
    project.schema_definition = current_def
    flag_modified(project, 'schema_definition')
    project.creation_stage = schemas.CreationStageEnum.GENERATING_DDL.value

    db.add(project)
    await db.commit()
    await db.refresh(project)

    # 清除缓存，确保前端立即看到状态变化
    await _invalidate_project_cache(project.project_id, user_id)

    # 获取数据库实例信息
    instance = await crud_database_instance.get(db, project.instance_id)

    # 调度 Celery 任务：DDL 生成 + 可选 ER 重新生成
    task_id = _dispatch_ddl_er_task(
        project_id=project.project_id,
        schema_text=new_schema,
        requirements=project.description,
        db_type=instance.db_type,
        db_name=instance.db_name,
        ai_model="gpt4",
        regenerate_er=schema_changed  # Schema 有变化时重新生成 ER 图
    )

    return schemas.ProjectAsyncResponse(
        project_id=project.project_id,
        project_name=project.project_name,
        status=project.project_status,
        message="Schema已确认，正在生成DDL..." + ("并更新ER图..." if schema_changed else ""),
        task_id=task_id
    )


# =========================================================
# 部署服务
# =========================================================

async def _execute_deployment(
    instance: Any,
    final_ddl: str,
    use_smart_parse: bool,
    user_id: int
) -> None:
    """执行 DDL 部署。"""
    await DBExecutorService.deploy(
        db_type=instance.db_type,
        db_name=instance.db_name,
        ddl=final_ddl,
        use_smart_parse=use_smart_parse,
        user_id=user_id
    )


async def _update_deployment_success(
    db: Session,
    project: Any,
    instance: Any,
    final_ddl: str,
    confirmed_schema: Optional[str]
) -> Any:
    """更新部署成功后的状态，并异步触发 DDL 向量化。"""
    update_data = {
        "project_status": "active",
        "creation_stage": schemas.CreationStageEnum.COMPLETED.value,
        "ddl_statement": final_ddl
    }

    if confirmed_schema:
        current_def = project.schema_definition or {}
        current_def['schema'] = confirmed_schema
        update_data["schema_definition"] = current_def

    await crud_project.update(db, project.project_id, **update_data)
    await crud_database_instance.update(db, instance, status='active')
    
    # 异步触发 DDL 向量化（不阻塞主流程）
    try:
        asyncio.create_task(
            rag_service.index_ddl(
                project_id=project.project_id,
                ddl_text=final_ddl
            )
        )
        log.info(f"[RAG] Triggered DDL indexing for project {project.project_id}")
    except Exception as e:
        # 向量化失败不影响主流程
        log.warning(f"[RAG] Failed to trigger DDL indexing: {e}")
    
    return await crud_project.get(db, project.project_id)


async def deploy_project_service(
    db: Session,
    project_id: int,
    user_id: int,
    deploy_data: schemas.ProjectDeployRequest
) -> schemas.ProjectDetailOut:
    """执行项目部署，接收用户确认的 DDL 并建库建表。"""
    # 1. 校验项目
    project = await _verify_project_ownership(db, project_id, user_id)

    # 2. 更新状态为"执行中"
    await crud_project.update(
        db, project_id,
        creation_stage=schemas.CreationStageEnum.EXECUTING_DDL.value
    )
    # 清除缓存，确保前端立即看到状态变化
    await _invalidate_project_cache(project_id, user_id)

    instance = await crud_database_instance.get(db, project.instance_id)
    final_ddl = deploy_data.confirmed_ddl or project.ddl_statement

    try:
        # 3. 执行部署
        await _execute_deployment(instance, final_ddl, deploy_data.use_smart_parse, user_id)

        # 4. 更新成功状态
        refreshed_project = await _update_deployment_success(
            db, project, instance, final_ddl, deploy_data.confirmed_schema
        )
        # 清除缓存，确保前端立即看到完成状态
        await _invalidate_project_cache(project_id, user_id)
        return schemas.ProjectDetailOut.model_validate(refreshed_project)

    except Exception as e:
        # 失败回滚状态
        await crud_project.update(
            db, project_id,
            creation_stage=schemas.CreationStageEnum.DDL_GENERATED.value
        )
        # 清除缓存，确保前端看到回滚后的状态
        await _invalidate_project_cache(project_id, user_id)
        raise e


# =========================================================
# 项目列表与详情
# =========================================================

async def get_projects_list_service(
    db: Session,
    user_id: int,
    search: Optional[str],
    page: int,
    page_size: int
) -> schemas.PaginatedProjectList:
    """获取指定用户的项目列表，支持分页和搜索。"""
    # 生成缓存键，包含搜索条件和分页参数
    cache_key = redis_key_manager.get_project_list_key(user_id, search, page, page_size)

    # 定义从数据库获取项目列表的函数
    async def fetch_project_list():
        log.info(f"Cache miss for project list (user: {user_id}, page: {page}), fetching from database")
        skip = (page - 1) * page_size
        total = await crud_project.get_total_count_by_user(db, user_id, search)
        items = await crud_project.get_by_user(db, user_id, skip, page_size, search)

        return schemas.PaginatedProjectList(
            total=total,
            page=page,
            page_size=page_size,
            items=[schemas.ProjectListOne.model_validate(i) for i in items]
        )

    # 使用缓存服务获取或设置数据，TTL设为10秒
    cache_result = await cache_service.get_or_set(cache_key, fetch_project_list, ttl=10)

    # 检查缓存结果是否有效（None 或空字符串都视为无效）
    if cache_result.data is None or cache_result.data == "":
        # 如果缓存中没有数据，直接从数据库获取
        return await fetch_project_list()

    # 确保返回的是PaginatedProjectList对象
    if isinstance(cache_result.data, dict):
        # 转换items列表中的字典为ProjectListOne对象
        items = []
        for item in cache_result.data.get('items', []):
            if isinstance(item, dict):
                items.append(schemas.ProjectListOne(**item))
            else:
                items.append(item)
        cache_result.data['items'] = items
        return schemas.PaginatedProjectList(**cache_result.data)

    return cache_result.data


async def get_project_detail_service(
    db: Session,
    project_id: int,
    user_id: int
) -> schemas.ProjectDetailOut:
    """获取项目详情，校验用户权限。"""
    # 生成缓存键
    cache_key = redis_key_manager.get_project_info_key(project_id)

    # 定义从数据库获取项目信息的函数
    async def fetch_project_data():
        log.info(f"Cache miss for project {project_id}, fetching from database")
        db_obj = await _verify_project_ownership(db, project_id, user_id)
        return schemas.ProjectDetailOut.model_validate(db_obj)

    # 使用缓存服务获取或设置数据，TTL设为10秒
    cache_result = await cache_service.get_or_set(cache_key, fetch_project_data, ttl=10)

    # 检查缓存结果是否有效（None 或空字符串都视为无效）
    if cache_result.data is None or cache_result.data == "":
        raise ItemNotFoundException("项目未找到或访问被拒绝")

    # 确保返回的是ProjectDetailOut对象
    if isinstance(cache_result.data, dict):
        return schemas.ProjectDetailOut(**cache_result.data)

    return cache_result.data


# =========================================================
# 更新项目信息
# =========================================================

async def update_project_info_service(
    db: Session,
    project_id: int,
    user_id: int,
    update_data: Dict[str, Any]
) -> schemas.ProjectDetailOut:
    """更新项目基本信息（名称或描述），不涉及 AI 生成或 DDL 执行。"""
    db_obj = await _verify_project_ownership(db, project_id, user_id)

    if db_obj.project_status == 'deleted':
        raise OperationNotPermittedException("无法更新已删除的项目")

    updated_obj = await crud_project.update(db, project_id, **update_data)

    # 清除相关缓存，确保数据一致性
    await _invalidate_project_cache(project_id, user_id)

    return schemas.ProjectDetailOut.model_validate(updated_obj)


# =========================================================
# 删除项目
# =========================================================

async def confirm_delete_project_service(
    db: Session,
    project_id: int,
    user_id: int,
    confirmation_text: str
) -> schemas.ConfirmationTokenResponse:
    """
    生成项目删除确认 Token。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。
        user_id (int): 用户 ID。
        confirmation_text (str): 确认文本，必须为 'DELETE'。

    Returns:
        schemas.ConfirmationTokenResponse: 包含确认 Token 及过期时间。

    Raises:
        ValidationException: 确认文本错误。
        ItemNotFoundException: 项目不存在或无权限。
    """
    if confirmation_text != "DELETE":
        raise ValidationException("确认文本必须是 'DELETE'")

    await _verify_project_ownership(db, project_id, user_id)

    payload = {"sub": str(user_id), "project_id": project_id}
    token = create_access_token(payload)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=config.jwt.token_expire_time_seconds)

    return schemas.ConfirmationTokenResponse(confirmation_token=token, expires_at=expires_at)


async def _verify_delete_token(token: str, user_id: int, project_id: int) -> bool:
    """验证删除确认 Token。"""
    try:
        payload = jwt.decode(
            token,
            config.jwt.secret_key,
            algorithms=[config.jwt.algorithm]
        )

        token_sub = payload.get("sub")
        token_pid = payload.get("project_id")

        if str(token_sub) != str(user_id):
            return False
        if token_pid is None or int(token_pid) != int(project_id):
            return False

        return True
    except (JWTError, ValueError, TypeError, AttributeError):
        return False


async def _release_user_quota(db: Session, user_id: int) -> None:
    """释放用户配额。"""
    user = await crud_user_account.get(db, user_id)
    if user and user.used_databases > 0:
        await crud_user_account.update(db, user, used_databases=user.used_databases - 1)


async def delete_project_service(
    db: Session,
    project_id: int,
    user_id: int,
    confirmation_token: str
) -> bool:
    """执行项目删除操作，校验 Token 并释放用户额度。"""
    if not await _verify_delete_token(confirmation_token, user_id, project_id):
        raise OperationNotPermittedException("无效的令牌")

    project = await crud_project.get(db, project_id)
    if not project or project.project_status == 'deleted':
        return True

    await crud_project.change_status(db, project_id, 'deleted')
    await _release_user_quota(db, user_id)
    
    # 清除相关缓存，确保数据一致性
    await _invalidate_project_cache(project_id, user_id)

    return True


# =========================================================
# 重新生成 ER 图
# =========================================================

async def regenerate_project_er_service(
    db: Session,
    project_id: int,
    user_id: int,
    schema_text: str,
    ai_model: str = "gpt4"
) -> schemas.ProjectAsyncResponse:
    """
    更新项目的 Schema 定义，并异步重新生成 Mermaid ER 代码。

    流程：
    1. 保存新的 Schema 到数据库
    2. 调度 Celery 任务重新生成 ER 图
    3. 返回 task_id 供前端查询状态
    """
    from sqlalchemy.orm.attributes import flag_modified
    
    project = await _verify_project_ownership(db, project_id, user_id)

    # 保存新的 Schema - 创建新字典以确保 SQLAlchemy 检测到变化
    current_def = dict(project.schema_definition or {})
    current_def['schema'] = schema_text
    project.schema_definition = current_def
    flag_modified(project, 'schema_definition')

    db.add(project)
    await db.commit()
    await db.refresh(project)

    # 清除项目缓存，确保前端能立即看到更新
    await _invalidate_project_cache(project_id, user_id)

    # 调度 Celery 任务重新生成 ER 图
    task_id = _dispatch_er_only_task(
        project_id=project_id,
        schema_text=schema_text,
        ai_model=ai_model
    )
    log.info(f"[RegenER] Dispatched ER regeneration for Project {project_id}, task_id={task_id}")

    return schemas.ProjectAsyncResponse(
        project_id=project.project_id,
        project_name=project.project_name,
        status=project.project_status,
        message="正在重新生成 ER 图...",
        task_id=task_id
    )


# =========================================================
# 任务状态查询服务
# =========================================================

async def get_task_status_service(task_id: str) -> Dict[str, Any]:
    """
    查询 Celery 任务状态。

    Args:
        task_id: Celery 任务 ID

    Returns:
        任务状态信息字典
    """
    return get_task_status(task_id)
