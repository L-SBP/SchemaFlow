# backend/app/tasks/ai_generation_tasks.py

"""
AI 生成任务模块

定义 Schema、DDL、ER 图生成的 Celery 异步任务。
支持任务链式调用和状态跟踪。

任务流程：
1. generate_schema_task: 用户输入 -> 生成 Schema
2. generate_er_task: Schema -> 生成 ER 图（可与 DDL 并行）
3. generate_ddl_task: 用户确认 Schema -> 生成 DDL
4. regenerate_er_task: 用户修改 Schema -> 重新生成 ER 图
"""

import asyncio
from typing import Optional, Dict, Any
from celery import shared_task, chain, group
from celery.utils.log import get_task_logger

from celery_app import celery_app
from core.config import config
from core.database import PsqlHelper
from core.log import log
from crud.crud_project import crud_project
from schema import project as schemas
from service.ai_service import AIService
from redis_client.redis_keys import redis_key_manager
from redis_client.cache_service import cache_service

logger = get_task_logger(__name__)


# =========================================================
# 辅助函数：同步运行异步代码
# =========================================================

def run_async(coro):
    """在同步环境中运行异步协程。"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _update_project_field(project_id: int, **update_fields) -> bool:
    """更新项目字段的通用方法，同时清除相关缓存。"""
    temp_engine = PsqlHelper._get_async_engine(config.db)
    try:
        async with PsqlHelper.get_session(temp_engine) as session:
            project = await crud_project.update(session, project_id, **update_fields)
            user_id = project.user_id if project else None
        
        # 清除项目相关的 Redis 缓存
        if project and user_id:
            cache_invalidated = await _invalidate_project_cache(project_id, user_id)
            if not cache_invalidated:
                log.warning(f"[Cache] Cache invalidation failed for project {project_id} after field update")
                logger.warning(f"[Task] Cache invalidation failed for project {project_id} after field update")
        
        return True
    except Exception as e:
        logger.error(f"[Task] Failed to update project {project_id}: {e}")
        return False
    finally:
        await temp_engine.dispose()


async def _invalidate_project_cache(project_id: int, user_id: int = None) -> bool:
    """清除项目相关的所有缓存。"""
    try:
        # 1. 清除项目详情缓存
        project_info_key = redis_key_manager.get_project_info_key(project_id)
        log.info(f"[Cache] Processing cache invalidation for project {project_id}")
        
        # 检查缓存键是否存在
        key_exists = await cache_service.exists(project_info_key)
        log.info(f"[Cache] Project info cache key {project_info_key} exists: {key_exists}")
        
        if key_exists:
            log.info(f"[Cache] Attempting to delete cache key: {project_info_key}")
            cache_deleted = await cache_service.delete(project_info_key)
            log.info(f"[Cache] Delete operation result for project info cache {project_info_key}: {cache_deleted}")
            
            if cache_deleted:
                logger.info(f"[Task] Successfully cleared project info cache for project {project_id}")
            else:
                log.error(f"[Cache] Failed to delete project info cache {project_info_key} despite it existing")
                logger.error(f"[Task] Failed to clear project info cache for project {project_id}")
        else:
            log.info(f"[Cache] Project info cache key {project_info_key} does not exist, no deletion needed")
            cache_deleted = True  # 键不存在也算删除成功
        
        # 2. 如果有 user_id，清除该用户的所有项目列表缓存
        list_cache_deleted = True
        if user_id:
            project_list_pattern = redis_key_manager.generate_key(
                redis_key_manager.USER_PREFIX, "projects", str(user_id), "*"
            )
            log.info(f"[Cache] Attempting to delete cache pattern: {project_list_pattern}")
            pattern_deleted_count = await cache_service.delete_pattern(project_list_pattern)
            log.info(f"[Cache] Delete pattern operation result for user {user_id} pattern {project_list_pattern}: {pattern_deleted_count} keys deleted")
            
            if pattern_deleted_count >= 0:
                logger.info(f"[Task] Cleared project list cache for user {user_id}")
            else:
                list_cache_deleted = False
                log.warning(f"[Cache] Failed to delete project list cache pattern {project_list_pattern}")
                logger.warning(f"[Task] Failed to clear project list cache for user {user_id}")

        log.info(f"[Cache] Completed cache invalidation for project {project_id}, user {user_id}")
        return cache_deleted and list_cache_deleted
    except Exception as e:
        log.error(f"[Cache] Exception occurred during cache invalidation for project {project_id}: {e}")
        logger.warning(f"[Task] Failed to clear cache for project {project_id}: {e}")
        return False


async def _get_project(project_id: int) -> Optional[Dict[str, Any]]:
    """获取项目信息。"""
    temp_engine = PsqlHelper._get_async_engine(config.db)
    try:
        async with PsqlHelper.get_session(temp_engine) as session:
            project = await crud_project.get(session, project_id)
            if project:
                return {
                    "project_id": project.project_id,
                    "schema_definition": project.schema_definition,
                    "description": project.description,
                    "ddl_statement": project.ddl_statement,
                    "er_diagram_code": project.er_diagram_code,
                    "creation_stage": project.creation_stage,
                    "project_status": project.project_status,
                }
        return None
    finally:
        await temp_engine.dispose()


# =========================================================
# 任务 1: Schema 生成
# =========================================================

@celery_app.task(
    bind=True,
    name="tasks.generate_schema",
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=300,
    time_limit=360
)
def generate_schema_task(
    self,
    project_id: int,
    requirements: str,
    db_name: str,
    db_type: str,
    ai_model: str = "gpt4"
) -> Dict[str, Any]:
    """
    Celery 任务：生成 Schema。
    
    Args:
        project_id: 项目 ID
        requirements: 用户需求描述
        db_name: 数据库名称
        db_type: 数据库类型
        ai_model: AI 模型标识
        
    Returns:
        包含生成结果的字典
    """
    logger.info(f"[Task-Schema] Starting for Project {project_id}, task_id={self.request.id}")
    
    try:
        # 调用 AI 服务生成 Schema
        schema_res = AIService.generate_schema(
            requirements=requirements,
            db_name=db_name,
            db_type="mysql",  # 内部统一用 mysql 格式生成 schema
            ai_model=ai_model
        )
        
        if not schema_res:
            logger.error(f"[Task-Schema] Failed to generate schema for Project {project_id}")
            # 更新项目状态为失败
            run_async(_update_project_field(
                project_id,
                creation_stage=schemas.CreationStageEnum.INITIALIZING.value,
                project_status="schema_generation_failed"
            ))
            return {
                "success": False,
                "project_id": project_id,
                "error": "Schema generation returned empty result"
            }
        
        # 保存 Schema 到数据库
        async def save_schema():
            temp_engine = PsqlHelper._get_async_engine(config.db)
            try:
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
                            logger.info(f"[Task-Schema] SUCCESS for Project {project_id}")
                
                # 事务提交成功后，重新获取最新的项目信息并清除缓存
                async with PsqlHelper.get_session(temp_engine) as session:
                    project = await crud_project.get(session, project_id)
                    if project:
                        log.info(f"[Task-Schema] About to invalidate cache for Project {project_id}, user {project.user_id}")
                        await _invalidate_project_cache(project_id, project.user_id)
            finally:
                await temp_engine.dispose()
        
        run_async(save_schema())
        
        return {
            "success": True,
            "project_id": project_id,
            "schema_text": schema_res,
            "db_name": db_name,
            "ai_model": ai_model
        }
        
    except Exception as e:
        logger.error(f"[Task-Schema] Error for Project {project_id}: {e}")
        # 重试逻辑
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        # 最终失败，更新状态
        run_async(_update_project_field(
            project_id,
            creation_stage=schemas.CreationStageEnum.INITIALIZING.value,
            project_status="schema_generation_failed"
        ))
        return {
            "success": False,
            "project_id": project_id,
            "error": str(e)
        }


# =========================================================
# 任务 2: ER 图生成
# =========================================================

@celery_app.task(
    bind=True,
    name="tasks.generate_er",
    max_retries=2,
    default_retry_delay=20,
    soft_time_limit=60,
    time_limit=90
)
def generate_er_task(
    self,
    project_id: int,
    schema_text: str,
    ai_model: str = "gpt4"
) -> Dict[str, Any]:
    """
    Celery 任务：生成 ER 图。
    
    ER 图生成失败不影响主流程，仅记录失败状态。
    
    Args:
        project_id: 项目 ID
        schema_text: Schema 文本
        ai_model: AI 模型标识
        
    Returns:
        包含生成结果的字典
    """
    logger.info(f"[Task-ER] Starting for Project {project_id}, task_id={self.request.id}")
    
    try:
        # 调用 AI 服务生成 ER 图
        er_code = AIService.generate_mermaid_code(
            schema_text=schema_text,
            ai_model=ai_model
        )
        
        if not er_code:
            logger.warning(f"[Task-ER] Empty ER code for Project {project_id}")
            return {
                "success": False,
                "project_id": project_id,
                "error": "ER diagram generation returned empty result"
            }
        
        # 保存 ER 图到数据库
        run_async(_update_project_field(project_id, er_diagram_code=er_code))
        
        # 清除项目详情缓存，确保前端能立即看到最新数据
        async def invalidate_cache():
            temp_engine = PsqlHelper._get_async_engine(config.db)
            try:
                async with PsqlHelper.get_session(temp_engine) as session:
                    db_project = await crud_project.get(session, project_id)
                    if db_project:
                        log.info(f"[Task-ER] About to invalidate cache for Project {project_id}, user {db_project.user_id}")
                        await _invalidate_project_cache(project_id, db_project.user_id)
                        logger.info(f"[Task-ER] Cache invalidated for Project {project_id}")
            finally:
                await temp_engine.dispose()
        
        run_async(invalidate_cache())
        
        logger.info(f"[Task-ER] SUCCESS for Project {project_id}")
        return {
            "success": True,
            "project_id": project_id,
            "er_code": er_code
        }
        
    except Exception as e:
        logger.error(f"[Task-ER] Error for Project {project_id}: {e}")
        # ER 图生成失败不重试，不影响主流程
        return {
            "success": False,
            "project_id": project_id,
            "error": str(e)
        }


# =========================================================
# 任务 3: DDL 生成
# =========================================================

@celery_app.task(
    bind=True,
    name="tasks.generate_ddl",
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=150,
    time_limit=180
)
def generate_ddl_task(
    self,
    project_id: int,
    schema_text: str,
    requirements: str,
    db_type: str,
    db_name: str,
    ai_model: str = "gpt4"
) -> Dict[str, Any]:
    """
    Celery 任务：生成 DDL。
    
    Args:
        project_id: 项目 ID
        schema_text: 用户确认的 Schema 文本
        requirements: 需求描述
        db_type: 数据库类型
        db_name: 数据库名称
        ai_model: AI 模型标识
        
    Returns:
        包含生成结果的字典
    """
    logger.info(f"[Task-DDL] Starting for Project {project_id}, task_id={self.request.id}")
    
    try:
        # 调用 AI 服务生成 DDL
        ddl_res = AIService.generate_ddl(
            schema_text=schema_text,
            requirements=requirements,
            db_type=db_type,
            ai_model=ai_model
        )
        
        if not ddl_res:
            logger.error(f"[Task-DDL] Failed to generate DDL for Project {project_id}")
            run_async(_update_project_field(
                project_id,
                creation_stage=schemas.CreationStageEnum.SCHEMA_GENERATED.value,
                project_status="ddl_generation_failed"
            ))
            return {
                "success": False,
                "project_id": project_id,
                "error": "DDL generation returned empty result"
            }
        
        # 构建完整 DDL（添加数据库创建语句）
        if db_type == 'mysql':
            full_ddl = f"CREATE DATABASE IF NOT EXISTS `{db_name}`;\nUSE `{db_name}`;\n\n{ddl_res}"
        else:
            full_ddl = ddl_res
        
        # 保存 DDL 到数据库
        run_async(_update_project_field(
            project_id,
            ddl_statement=full_ddl,
            creation_stage=schemas.CreationStageEnum.DDL_GENERATED.value,
            project_status=schemas.ProjectStatusEnum.PENDING_CONFIRMATION.value
        ))
        
        # 清除项目详情缓存，确保前端能立即看到最新数据
        async def invalidate_cache():
            temp_engine = PsqlHelper._get_async_engine(config.db)
            try:
                async with PsqlHelper.get_session(temp_engine) as session:
                    db_project = await crud_project.get(session, project_id)
                    if db_project:
                        log.info(f"[Task-DDL] About to invalidate cache for Project {project_id}, user {db_project.user_id}")
                        await _invalidate_project_cache(project_id, db_project.user_id)
                        logger.info(f"[Task-DDL] Cache invalidated for Project {project_id}")
            finally:
                await temp_engine.dispose()
        
        run_async(invalidate_cache())
        
        logger.info(f"[Task-DDL] SUCCESS for Project {project_id}")
        return {
            "success": True,
            "project_id": project_id,
            "ddl_statement": full_ddl
        }
        
    except Exception as e:
        logger.error(f"[Task-DDL] Error for Project {project_id}: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        run_async(_update_project_field(
            project_id,
            creation_stage=schemas.CreationStageEnum.SCHEMA_GENERATED.value,
            project_status="ddl_generation_failed"
        ))
        return {
            "success": False,
            "project_id": project_id,
            "error": str(e)
        }


# =========================================================
# 任务 4: Schema + ER 流水线（创建项目时使用）
# =========================================================

@celery_app.task(
    bind=True,
    name="tasks.schema_er_pipeline",
    soft_time_limit=600,
    time_limit=660
)
def schema_er_pipeline_task(
    self,
    project_id: int,
    requirements: str,
    db_name: str,
    db_type: str,
    ai_model: str = "gpt4"
) -> Dict[str, Any]:
    """
    Celery 任务：Schema + ER 生成流水线。
    
    流程：生成 Schema -> 生成 ER 图
    
    Args:
        project_id: 项目 ID
        requirements: 用户需求描述
        db_name: 数据库名称
        db_type: 数据库类型
        ai_model: AI 模型标识
        
    Returns:
        包含流水线执行结果的字典
    """
    logger.info(f"[Pipeline-Schema-ER] Starting for Project {project_id}")
    
    # Step 1: 生成 Schema
    schema_result = generate_schema_task(
        project_id=project_id,
        requirements=requirements,
        db_name=db_name,
        db_type=db_type,
        ai_model=ai_model
    )
    
    if not schema_result.get("success"):
        logger.error(f"[Pipeline] Schema generation failed for Project {project_id}")
        return {
            "success": False,
            "project_id": project_id,
            "stage": "schema",
            "error": schema_result.get("error")
        }
    
    # Step 2: 生成 ER 图
    schema_text = schema_result.get("schema_text", "")
    if schema_text:
        er_result = generate_er_task(
            project_id=project_id,
            schema_text=schema_text,
            ai_model=ai_model
        )
        # ER 图失败不影响整体流程
        if not er_result.get("success"):
            logger.warning(f"[Pipeline] ER generation failed for Project {project_id}, continuing...")
    
    logger.info(f"[Pipeline-Schema-ER] Completed for Project {project_id}")
    return {
        "success": True,
        "project_id": project_id,
        "schema_text": schema_text,
        "stage": "completed"
    }


# =========================================================
# 任务 5: DDL + ER 并行生成（用户确认 Schema 后使用）
# =========================================================

@celery_app.task(
    bind=True,
    name="tasks.ddl_er_parallel",
    soft_time_limit=600,
    time_limit=660
)
def ddl_er_parallel_task(
    self,
    project_id: int,
    schema_text: str,
    requirements: str,
    db_type: str,
    db_name: str,
    ai_model: str = "gpt4",
    regenerate_er: bool = True
) -> Dict[str, Any]:
    """
    Celery 任务：DDL 和 ER 图并行生成。
    
    当用户确认或修改 Schema 后调用此任务。
    
    Args:
        project_id: 项目 ID
        schema_text: 用户确认的 Schema 文本
        requirements: 需求描述
        db_type: 数据库类型
        db_name: 数据库名称
        ai_model: AI 模型标识
        regenerate_er: 是否重新生成 ER 图
        
    Returns:
        包含执行结果的字典
    """
    logger.info(f"[Pipeline-DDL-ER] Starting for Project {project_id}, regenerate_er={regenerate_er}")
    
    results = {"project_id": project_id}
    
    # 生成 DDL（必须）
    ddl_result = generate_ddl_task(
        project_id=project_id,
        schema_text=schema_text,
        requirements=requirements,
        db_type=db_type,
        db_name=db_name,
        ai_model=ai_model
    )
    results["ddl"] = ddl_result
    
    # 如果需要重新生成 ER 图
    if regenerate_er:
        er_result = generate_er_task(
            project_id=project_id,
            schema_text=schema_text,
            ai_model=ai_model
        )
        results["er"] = er_result
    
    success = ddl_result.get("success", False)
    results["success"] = success
    
    logger.info(f"[Pipeline-DDL-ER] Completed for Project {project_id}, success={success}")
    return results


# =========================================================
# 任务状态查询辅助函数
# =========================================================

def get_task_status(task_id: str, project_id: int = None) -> Dict[str, Any]:
    """
    查询 Celery 任务状态，并可选地返回项目的业务状态。
    
    Args:
        task_id: Celery 任务 ID
        project_id: 可选，项目 ID（用于获取项目的 creation_stage）
        
    Returns:
        任务状态信息字典，包含：
        - task_id: 任务 ID
        - task_status: Celery 任务状态 (PENDING, STARTED, SUCCESS, FAILURE)
        - ready: 任务是否完成
        - successful: 任务是否成功
        - result: 任务结果（成功时）
        - error: 错误信息（失败时）
        - project_id: 项目 ID（如果提供）
        - creation_stage: 项目创建阶段（如果提供 project_id 且任务完成）
    """
    result = celery_app.AsyncResult(task_id)
    
    status_info = {
        "task_id": task_id,
        "task_status": result.status,  # Celery 任务状态
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
    }
    
    if result.ready():
        if result.successful():
            task_result = result.result
            status_info["result"] = task_result
            # 从任务结果中提取 project_id
            if task_result and isinstance(task_result, dict):
                project_id = task_result.get("project_id", project_id)
        else:
            status_info["error"] = str(result.result) if result.result else "Unknown error"
    
    # 如果有 project_id 且任务完成，获取项目的最新 creation_stage
    if project_id and result.ready():
        try:
            project_info = run_async(_get_project(project_id))
            if project_info:
                status_info["project_id"] = project_id
                status_info["creation_stage"] = project_info.get("creation_stage")
                status_info["project_status"] = project_info.get("project_status")
        except Exception as e:
            logger.warning(f"Failed to get project info for {project_id}: {e}")
    
    return status_info
