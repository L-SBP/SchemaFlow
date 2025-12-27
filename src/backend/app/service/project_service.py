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

# 缓存相关
from redis_client.redis_keys import redis_key_manager
from redis_client.cache_service import cache_service


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
# 后台任务：Schema 生成
# =========================================================

# TODO: [Celery] Schema 生成任务迁移
# 当前实现：FastAPI BackgroundTasks
# 后续优化：
#   1. 迁移到 Celery 异步任务，支持任务重试、超时控制
#   2. 添加任务状态跟踪（pending/running/success/failed）
#   3. 支持任务取消和进度查询 API
#   4. 配置独立的 AI 任务队列，避免阻塞其他任务
#   5. 设置合理的任务超时时间（建议 5 分钟）

async def _generate_and_save_schema(
    project_id: int,
    requirements: str,
    db_name: str,
    db_type: str,
    ai_model: str
) -> Optional[str]:
    """
    执行 AI Schema 生成并保存到数据库。
    
    【重要】此函数在后台任务中执行，使用独立的数据库会话。
    """
    log.info(f"[Task] Starting SCHEMA GENERATION for Project {project_id}...")
    loop = asyncio.get_event_loop()

    schema_res = await loop.run_in_executor(
        None, AIService.generate_schema, requirements, db_name, "mysql", ai_model
    )

    if not schema_res:
        log.error(f"[Task-Schema] Failed to generate schema for Project {project_id}")
        return None

    # 使用独立会话保存结果
    temp_engine = PsqlHelper._get_async_engine(config.db)
    async with PsqlHelper.get_session(temp_engine) as session:
        async with session.begin():
            project = await crud_project.get(session, project_id)
            if project:
                current_def = project.schema_definition or {}
                current_def['schema'] = schema_res
                current_def['generated_db_name'] = db_name
                project.schema_definition = current_def
                project.creation_stage = schemas.CreationStageEnum.SCHEMA_GENERATED.value
                session.add(project)
                log.info(f"[Task-Schema] SUCCESS for Project {project_id}. Saved to DB.")
    
    await temp_engine.dispose()
    return schema_res


# TODO: [Celery] ER 图生成任务迁移
# 当前实现：与 Schema 生成串联执行
# 业务约束：
#   - 必须在 Schema 生成成功后才能执行
#   - 与 DDL 生成互不依赖，可并行
# 后续优化：
#   1. 拆分为独立的 Celery 任务
#   2. 使用 Celery group 与 DDL 生成并行执行
#   3. ER 图生成失败不影响主流程，记录失败状态即可
#   4. 支持手动触发重新生成

async def _generate_and_save_er(project_id: int, schema_text: str, ai_model: str) -> None:
    """
    生成 ER 图并保存。错误不影响整体流程。
    """
    log.info(f"[Task-ER] Starting for Project {project_id}")
    loop = asyncio.get_event_loop()

    try:
        er_code = await loop.run_in_executor(
            None, AIService.generate_mermaid_code, schema_text, ai_model
        )
        if not er_code:
            raise InvalidOperationException(message="生成的ER图代码为空")

        temp_engine = PsqlHelper._get_async_engine(config.db)
        async with PsqlHelper.get_session(temp_engine) as session:
            await crud_project.update(session, project_id, er_diagram_code=er_code)
        await temp_engine.dispose()
        log.info(f"[Task-ER] SUCCESS for Project {project_id}")
    except Exception as e:
        log.error(f"[Task-ER] FAILED for Project {project_id}: {e}")


# TODO: [Celery] 任务编排优化
# 当前实现：Schema -> ER 串联执行
# 业务约束：
#   - Schema 是前置依赖，必须先成功生成 Schema
#   - ER 图和 DDL 都依赖 Schema，但互不依赖
#   - 用户修改 Schema 后必须重新生成 DDL
# 后续优化：
#   1. 使用 Celery canvas 组合任务：
#      chain(generate_schema.s(), group(generate_er.s(), generate_ddl.s()))
#   2. Schema 完成后 -> ER 和 DDL 可并行执行
#   3. 添加任务依赖关系管理
#   4. 支持任务失败后的回调通知（WebSocket/邮件）

async def task_pipeline_schema_flow(
    project_id: int,
    requirements: str,
    db_name: str,
    db_type: str,
    ai_model: str
) -> None:
    """串联 Schema 和 ER 生成流程。"""
    schema_text = await _generate_and_save_schema(
        project_id, requirements, db_name, db_type, ai_model
    )
    if schema_text:
        await _generate_and_save_er(project_id, schema_text, ai_model)


# =========================================================
# 后台任务：DDL 生成
# =========================================================

# TODO: [Celery] DDL 生成任务迁移
# 当前实现：FastAPI BackgroundTasks
# 业务约束：
#   - 必须在 Schema 生成/确认后才能执行
#   - 与 ER 图生成互不依赖，可并行
#   - 用户修改 Schema 后必须重新生成 DDL
# 后续优化：
#   1. 迁移到 Celery 异步任务
#   2. 支持任务重试机制（指数退避）
#   3. 添加任务进度回调（可通过 WebSocket 推送前端）
#   4. 配置任务优先级，用户付费项目可优先处理

async def task_generate_ddl_only(
    project_id: int,
    schema_text: str,
    requirements: str,
    db_type: str,
    db_name: str,
    ai_model: str = "gpt4"
) -> None:
    """后台任务：生成 DDL 语句。"""
    log.info(f"[Task] Starting DDL GENERATION for Project {project_id}...")
    loop = asyncio.get_event_loop()

    ddl_res = await loop.run_in_executor(
        None, AIService.generate_ddl, schema_text, requirements, db_type, ai_model
    )

    full_ddl = _build_full_ddl(ddl_res, db_type, db_name)

    temp_engine = PsqlHelper._get_async_engine(config.db)
    async with PsqlHelper.get_session(temp_engine) as session:
        await crud_project.update(
            session, project_id,
            ddl_statement=full_ddl,
            creation_stage=schemas.CreationStageEnum.DDL_GENERATED.value,
            project_status=schemas.ProjectStatusEnum.PENDING_CONFIRMATION.value
        )
    await temp_engine.dispose()


def _build_full_ddl(ddl_res: str, db_type: str, db_name: str) -> str:
    """根据数据库类型构建完整 DDL。"""
    if db_type == 'mysql':
        return f"CREATE DATABASE IF NOT EXISTS `{db_name}`;\nUSE `{db_name}`;\n\n{ddl_res}"
    return ddl_res


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
    background_tasks: BackgroundTasks
) -> schemas.ProjectAsyncResponse:
    """
    创建项目并异步生成 Schema/DDL。
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

    # 6. 调度后台任务
    # TODO: [Celery] 替换为 Celery 任务调度
    # 当前实现：background_tasks.add_task()
    # 后续优化：
    #   1. 使用 task_pipeline_schema_flow.delay() 或 .apply_async()
    #   2. 保存 task_id 到项目记录，便于状态查询
    #   3. 支持任务取消：revoke(task_id, terminate=True)
    #   4. 返回 task_id 给前端，用于轮询或 WebSocket 订阅
    background_tasks.add_task(
        task_pipeline_schema_flow,
        project_id=db_obj.project_id,
        requirements=requirements_text,
        db_name=temp_db_name,
        db_type=db_type,
        ai_model=ai_model
    )

    # 7. 更新用户配额
    await crud_user_account.update(db, user, used_databases=user.used_databases + 1)

    return schemas.ProjectAsyncResponse.model_validate(db_obj)


# =========================================================
# DDL 生成请求服务
# =========================================================

async def request_ddl_generation_service(
    db: Session,
    project_id: int,
    user_id: int,
    data: schemas.GenerateDDLRequest,
    background_tasks: BackgroundTasks
) -> schemas.ProjectAsyncResponse:
    """用户确认 Schema，后端触发 DDL 生成任务。"""
    project = await _verify_project_ownership(db, project_id, user_id)

    # 更新需求描述（如果有）
    if data.requirements:
        project.description = data.requirements

    # 更新 Schema
    current_def = project.schema_definition or {}
    current_def['schema'] = data.confirmed_schema
    project.schema_definition = current_def
    project.creation_stage = schemas.CreationStageEnum.GENERATING_DDL.value

    db.add(project)
    await db.commit()
    await db.refresh(project)

    # 获取数据库实例信息
    instance = await crud_database_instance.get(db, project.instance_id)

    # 触发后台任务
    # TODO: [Celery] 替换为 Celery 任务调度
    # 同 create_project_service 中的 TODO 注释
    background_tasks.add_task(
        task_generate_ddl_only,
        project_id=project.project_id,
        schema_text=data.confirmed_schema,
        requirements=project.description,
        db_type=instance.db_type,
        db_name=instance.db_name,
        ai_model="gpt4"
    )

    return schemas.ProjectAsyncResponse(
        project_id=project.project_id,
        project_name=project.project_name,
        status=project.project_status,
        message="Schema已确认，正在生成DDL并更新ER图..."
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
    """更新部署成功后的状态。"""
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

    instance = await crud_database_instance.get(db, project.instance_id)
    final_ddl = deploy_data.confirmed_ddl or project.ddl_statement

    try:
        # 3. 执行部署
        await _execute_deployment(instance, final_ddl, deploy_data.use_smart_parse, user_id)

        # 4. 更新成功状态
        refreshed_project = await _update_deployment_success(
            db, project, instance, final_ddl, deploy_data.confirmed_schema
        )
        return schemas.ProjectDetailOut.model_validate(refreshed_project)

    except Exception as e:
        # 失败回滚状态
        await crud_project.update(
            db, project_id,
            creation_stage=schemas.CreationStageEnum.DDL_GENERATED.value
        )
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
    
    # 使用缓存服务获取或设置数据，TTL设为300秒
    cache_result = await cache_service.get_or_set(cache_key, fetch_project_list, ttl=300)
    
    if cache_result.data is None:
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
    
    # 使用缓存服务获取或设置数据，TTL设为300秒
    cache_result = await cache_service.get_or_set(cache_key, fetch_project_data, ttl=300)
    
    if cache_result.data is None:
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
    # 1. 清除项目详情缓存
    project_info_key = redis_key_manager.get_project_info_key(project_id)
    await cache_service.delete(project_info_key)
    
    # 2. 清除用户的所有项目列表缓存（包含不同分页和搜索条件的所有列表）
    project_list_pattern = redis_key_manager.generate_key(redis_key_manager.USER_PREFIX, "projects", str(user_id), "*")
    await cache_service.delete_pattern(project_list_pattern)
    
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
    # 1. 清除项目详情缓存
    project_info_key = redis_key_manager.get_project_info_key(project_id)
    await cache_service.delete(project_info_key)
    
    # 2. 清除用户的所有项目列表缓存（包含不同分页和搜索条件的所有列表）
    project_list_pattern = redis_key_manager.generate_key(redis_key_manager.USER_PREFIX, "projects", str(user_id), "*")
    await cache_service.delete_pattern(project_list_pattern)
    
    return True


# =========================================================
# 重新生成 ER 图
# =========================================================

# TODO: [Celery] ER 图重新生成任务
# 当前实现：同步执行（在线程池中）
# 后续优化：
#   1. 迁移到 Celery 任务，立即返回、后台生成
#   2. 生成完成后通过 WebSocket 通知前端刷新
#   3. 支持用户查询生成状态

async def regenerate_project_er_service(
    db: Session,
    project_id: int,
    user_id: int,
    schema_text: str,
    ai_model: str = "gpt4"
) -> schemas.ProjectDetailOut:
    """更新项目的 Schema 定义，并重新生成 Mermaid ER 代码。"""
    project = await _verify_project_ownership(db, project_id, user_id)

    log.info(f"[RegenER] Regenerating ER for Project {project_id}...")
    loop = asyncio.get_event_loop()
    er_code = await loop.run_in_executor(
        None,
        AIService.generate_mermaid_code,
        schema_text,
        ai_model
    )

    current_def = project.schema_definition or {}
    current_def['schema'] = schema_text

    project.schema_definition = current_def
    project.er_diagram_code = er_code

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return schemas.ProjectDetailOut.model_validate(project)
