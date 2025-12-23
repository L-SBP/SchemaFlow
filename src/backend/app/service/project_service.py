"""
项目服务。

负责项目生命周期：生成 Schema、生成 DDL、部署、元数据更新、列表与详情、删除
等；集成 AI 生成器、数据库助手与 CRUD 层。
"""

# backend/app/service/project_service.py



import random
import string
import asyncio

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession as Session
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import BackgroundTasks

# 隐式绝对导入
from crud.crud_project import crud_project
from crud.crud_database_instance import crud_database_instance
from crud.crud_user_account import crud_user_account
from schema import project as schemas
from core.exceptions import ItemNotFoundException, OperationNotPermittedException, \
    ValidationException
from core.auth import  create_access_token
from core.config import config
from core.database import PsqlHelper
from core.log import log
import re
from pypinyin import lazy_pinyin, Style

from service.ai_service import AIService
from service.db_executor_service import DBExecutorService


# ==========================================
# 数据库名称生成
# ==========================================
def generate_meaningful_db_name(project_name: str, user_id: int) -> str:
    """
    根据项目名称和用户 ID 生成符合数据库命名规范的唯一数据库名。

    Args:
        project_name (str): 项目名称。
        user_id (int): 用户 ID。

    Returns:
        str: 生成的数据库名称。
    """
    """
    将项目名称转换为符合数据库命名规范的字符串 (拼音/英文 + 下划线)
    例如: "电商管理平台" -> "dianshang_guanli_pingtai_1_x82a"
    """
    # 1. 中文转拼音 (如: ['dian', 'shang', 'ping', 'tai'])
    #    英文单词保持不变
    pinyin_list = lazy_pinyin(project_name, style=Style.NORMAL)

    # 2. 拼接成字符串
    full_str = "_".join(pinyin_list)

    # 3. 清洗：只保留字母、数字和下划线，且转为小写
    clean_str = re.sub(r'[^a-zA-Z0-9_]', '_', full_str).lower()

    # 4. 去除连续的下划线
    clean_str = re.sub(r'_+', '_', clean_str).strip('_')

    # 5. 截断过长的前缀 (防止数据库名过长，保留前 40 字符)
    if len(clean_str) > 40:
        clean_str = clean_str[:40].rstrip('_')

    # 6. 加上 user_id 和短随机码 (确保全局唯一性)
    #    为什么还要随机码？因为用户可能创建两个都叫 "测试项目" 的项目
    short_random = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))

    return f"{clean_str}_{user_id}_{short_random}"


# ==============================================================================
# 后台任务：生成 Schema
# ==============================================================================
async def task_step_1_generate_schema(
    project_id: int, 
    requirements: str, 
    db_name: str, 
    db_type: str, 
    ai_model: str
):
    """
    后台任务：调用 SchemaGenerator 生成 Schema
    该任务不会直接执行建表，仅生成 Schema。
    Args:
        project_id (int): 项目 ID。
        requirements (str): 项目需求描述。
        db_name (str): 生成的数据库名称。
        db_type (str): 数据库类型（如 mysql）。
        ai_model (str): 使用的 AI 模型。

    Returns:
        None

    """

    # 1. 执行 AI 生成
    log.info(f"[Task] Starting SCHEMA GENERATION for Project {project_id}...")
    loop = asyncio.get_event_loop()

    # 调用生成 Schema
    schema_res = await loop.run_in_executor(
        None, AIService.generate_schema, requirements, db_name, "mysql", ai_model
    )

    if not schema_res:
        log.error(f"[Task-Schema] Failed to generate schema for Project {project_id}")
        return None

    # 2. 存入 PostgreSQL 的 project.schema_definition 字段
    # 使用独立的 Session，因为这是后台任务
    temp_engine = PsqlHelper._get_async_engine(config.db)
    async with PsqlHelper.get_session(temp_engine) as session:
        async with session.begin():
            project = await crud_project.get(session, project_id)
            if project:
                current_def = project.schema_definition or {}

                # 存入 Schema，不再存入 DDL
                current_def['schema'] = schema_res
                current_def['generated_db_name'] = db_name

                project.schema_definition = current_def

                project.creation_stage = schemas.CreationStageEnum.SCHEMA_GENERATED.value
                log.info(f"[Task-Schema] SUCCESS for Project {project_id}. Saved to DB.")


                session.add(project)
    await temp_engine.dispose()

    return schema_res


# ==============================================================================
# 后台任务：生成 DDL
# ==============================================================================
async def task_generate_ddl_only(
    project_id: int, 
    schema_text: str, 
    requirements: str, 
    db_type: str, 
    db_name: str,
    ai_model:str = "gpt4"
):
    log.info(f"[Task] Starting DDL GENERATION for Project {project_id}...")
    loop = asyncio.get_event_loop()

    # 调用生成 DDL
    ddl_res =  await loop.run_in_executor(
        None, AIService.generate_ddl, schema_text, requirements, db_type, ai_model
    )


    temp_engine = PsqlHelper._get_async_engine(config.db)
    async with PsqlHelper.get_session(temp_engine) as session:
        if db_type == 'mysql':
            # MySQL 需要显式创建数据库并切换
            full_ddl = f"CREATE DATABASE IF NOT EXISTS `{db_name}`;\nUSE `{db_name}`;\n\n{ddl_res}"
        else:
            # PostgreSQL 和 SQLite:
            # 1. 不支持 USE 语法。
            # 2. 部署脚本(DBExecutorService) 中已经内置了 Create Database/File 的逻辑。
            # 3. 这里只保留 AI 生成的建表语句即可。
            full_ddl = ddl_res
        await crud_project.update(session, project_id,
            ddl_statement=full_ddl,
            creation_stage=schemas.CreationStageEnum.DDL_GENERATED.value,
            project_status=schemas.ProjectStatusEnum.PENDING_CONFIRMATION.value
            )
    await temp_engine.dispose()


async def task_step_2_generate_er(project_id: int, schema_text: str, ai_model: str):
    """
    第二步：生成 ER 图 (廉价操作)
    错误不应该影响第一步的结果
    """
    log.info(f"[Task-ER] Starting for Project {project_id}")
    loop = asyncio.get_event_loop()

    try:
        er_code = await loop.run_in_executor(None, AIService.generate_mermaid_code, schema_text, ai_model)
        if not er_code:
            raise Exception("Empty ER code generated")

        temp_engine = PsqlHelper._get_async_engine(config.db)
        async with PsqlHelper.get_session(temp_engine) as session:
            # 同样移除这里的 session.begin() async with session.begin():
            await crud_project.update(session, project_id, er_diagram_code=er_code)
        await temp_engine.dispose()
        log.info(f"[Task-ER] SUCCESS for Project {project_id}")
    except Exception as e:
        # 核心逻辑：捕获异常，仅记录日志，不影响项目整体进度
        log.error(f"[Task-ER] FAILED for Project {project_id}: {e}")


async def task_pipeline_schema_flow(project_id, requirements, db_name, db_type, ai_model):
    """
    串联 Schema 和 ER，但保持物理独立
    """
    # 执行第一步：Schema (昂贵)
    schema_text = await task_step_1_generate_schema(project_id, requirements, db_name, db_type, ai_model)

    # 只有第一步成功了，才跑第二步
    if schema_text:
        await task_step_2_generate_er(project_id, schema_text, ai_model)

# ==============================================================================
# 创建项目：异步执行ddl语句
# ==============================================================================
async def create_project_service(
    db: Session,
    project_in: schemas.ProjectCreate,
    user_id: int,
    background_tasks: BackgroundTasks
) -> schemas.ProjectAsyncResponse:
    """
    创建项目并异步生成 Schema/DDL。

    Args:
        db (Session): 数据库会话。
        project_in (schemas.ProjectCreate): 项目创建参数。
        user_id (int): 用户 ID。
        background_tasks (BackgroundTasks): 后台任务对象。

    Returns:
        schemas.ProjectAsyncResponse: 项目异步创建响应。

    Raises:
        ItemNotFoundException: 用户不存在。
        OperationNotPermittedException: 超出配额。
    """
    # ... (前面的配额检查代码保持不变) ...

    # 检查用户额度
    user = await crud_user_account.get(db, user_id)
    if not user:
        raise ItemNotFoundException("User not found")
    if user.used_databases >= user.max_databases:
        raise OperationNotPermittedException("Quota exceeded.")

    project_data = project_in.model_dump()
    # 弹出db_type等属性，因为后端数据库没有这个属性
    db_type = project_data.pop('db_type')
    ai_model = project_data.pop('ai_model', 'gpt4')
    requirements_text = project_data.get('description', '')
    project_name = project_data.get('project_name', 'project')

    # 生成 DB Name，但不创建物理库
    temp_db_name = generate_meaningful_db_name(project_name, user_id)

    # 根据 db_type 动态获取配置的 host 和 port
    target_host = "127.0.0.1"  # 默认回退值
    target_port = 3306  # 默认回退值

    if db_type == 'mysql':
        target_host = config.mysql.host
        target_port = config.mysql.port
    elif db_type == 'postgresql':
        target_host = config.postgresql.host
        target_port = config.postgresql.port
    # 如果有 sqlite 或其他类型，可以在此扩展，sqlite 通常不需要 port

    # 1. 创建 DatabaseInstance (占位)
    new_instance = await crud_database_instance.create(
        db,
        db_type=db_type,
        db_host=target_host,
        db_port=target_port,
        db_name=temp_db_name,  # 此时物理库还未创建
        db_username=f"test_{user_id}",
        db_password="User_secure_2025",
        status="inactive"  # 还没真正激活
    )

    # 2. 创建 Project，初始阶段设为 GENERATING_SCHEMA
    project_data['user_id'] = user_id
    project_data['instance_id'] = new_instance.instance_id
    project_data['project_status'] = 'initializing'

    # [关键修复] 设置初始阶段为 GENERATING_SCHEMA，并使用 .value
    project_data['creation_stage'] = schemas.CreationStageEnum.GENERATING_SCHEMA.value

    db_obj = await crud_project.create(db, **project_data)

    # 3. 调度“只生成”任务
    background_tasks.add_task(
        task_pipeline_schema_flow, # 封装一个串联逻辑
        project_id=db_obj.project_id,
        requirements=requirements_text,
        db_name=temp_db_name,
        db_type=db_type,
        ai_model=ai_model
    )

    # 更新配额 (虽然还没最终建库，但占用了生成资源，先预扣)
    await crud_user_account.update(db, user, used_databases=user.used_databases + 1)

    return schemas.ProjectAsyncResponse.model_validate(db_obj)


# ==============================================================================
# 请求生成 DDL
# ==============================================================================
async def request_ddl_generation_service(
    db: Session,
    project_id: int,
    user_id: int,
    data: schemas.GenerateDDLRequest,
    background_tasks: BackgroundTasks
) -> schemas.ProjectAsyncResponse:
    """
    用户确认 Schema，后端触发 DDL 生成任务。
    """
    project = await crud_project.get(db, project_id)
    if not project or project.user_id != user_id:
        raise ItemNotFoundException("Project not found")

    # 允许从 Schema Generated 状态或者 Initializing 状态继续
    # 如果用户修改了需求描述，更新它
    if data.requirements:
        project.description = data.requirements

    # 更新当前 Schema 到数据库 (用户可能修改了 Schema)
    current_def = project.schema_definition or {}
    current_def['schema'] = data.confirmed_schema

    # [修复] 更新状态为 GENERATING_DDL (.value)
    project.schema_definition = current_def
    project.creation_stage = schemas.CreationStageEnum.GENERATING_DDL.value

    db.add(project)
    await db.commit()
    await db.refresh(project)

    # 获取关联信息
    instance = await crud_database_instance.get(db, project.instance_id)

    # 触发后台任务：生成 DDL
    background_tasks.add_task(
        task_generate_ddl_only,
        project_id=project.project_id,
        schema_text=data.confirmed_schema,
        requirements=project.description,  # 使用(可能更新过的)需求
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





# ==============================================================================
# 部署执行
# ==============================================================================
async def deploy_project_service(
    db: Session,
    project_id: int,
    user_id: int,
    deploy_data: schemas.ProjectDeployRequest
) -> schemas.ProjectResponse:
    """
    执行项目部署，接收用户确认的 DDL 并建库建表。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。
        user_id (int): 用户 ID。
        deploy_data (schemas.ProjectDeployRequest): 部署请求参数。

    Returns:
        schemas.ProjectResponse: 项目部署后的响应。

    Raises:
        ItemNotFoundException: 项目不存在或无权限。
        ValidationException: DDL 预处理失败。
        DatabaseOperationFailedException: 部署执行失败。
    """
    """
    接收用户确认的 DDL，执行建库和建表操作，将项目状态改为 Active。
    支持通过 use_smart_parse 参数控制是否启用方言转换和拓扑排序。
    """
    # TODO: 后续支持多种数据库时，需要将执行逻辑抽离出project_service代码
    # 1. 校验项目
    project = await crud_project.get(db, project_id)
    if not project or project.user_id != user_id:
        raise ItemNotFoundException("Project not found")

    # 2. 更新状态为“执行中”
    await crud_project.update(db, project_id, creation_stage=schemas.CreationStageEnum.EXECUTING_DDL.value)

    instance = await crud_database_instance.get(db, project.instance_id)
    final_ddl = deploy_data.confirmed_ddl or project.ddl_statement

    try:
        # 3. 调用 DDL 执行服务 (关键解耦点)
        await DBExecutorService.deploy(
            db_type=instance.db_type,
            db_name=instance.db_name,
            ddl=final_ddl,
            use_smart_parse=deploy_data.use_smart_parse
        )

        # 4. 更新部署成功后的业务状态
        update_data = {
            "project_status": "active",
            "creation_stage": schemas.CreationStageEnum.COMPLETED.value,
            "ddl_statement": final_ddl
        }

        # TODO:后续更改顺序，先存储前端给的更新的schema，以免造成ddl执行失败导致schema也更新失败
        if deploy_data.confirmed_schema:
            current_def = project.schema_definition or {}
            current_def['schema'] = deploy_data.confirmed_schema
            update_data["schema_definition"] = current_def

        await crud_project.update(db, project_id, **update_data)
        await crud_database_instance.update(db, instance, status='active')

        refreshed_project = await crud_project.get(db, project_id)
        return schemas.ProjectResponse(data=schemas.ProjectDetailOut.model_validate(refreshed_project))

    except Exception as e:
        # 失败回滚业务状态
        await crud_project.update(db, project_id, creation_stage=schemas.CreationStageEnum.DDL_GENERATED.value)
        raise e



# --- 项目列表 ---
async def get_projects_list_service(
    db: Session, 
    user_id: int, 
    search: Optional[str], 
    page: int, 
    page_size: int
) -> schemas.PaginatedProjectList:
    """
    获取指定用户的项目列表，支持分页和搜索。

    Args:
        db (Session): 数据库会话。
        user_id (int): 用户 ID。
        search (Optional[str]): 搜索关键字。
        page (int): 页码。
        page_size (int): 每页数量。

    Returns:
        schemas.PaginatedProjectList: 分页后的项目列表。
    """
    skip = (page - 1) * page_size
    total = await crud_project.get_total_count_by_user(db, user_id, search)
    items = await crud_project.get_by_user(db, user_id, skip, page_size, search)

    return schemas.PaginatedProjectList(
        total=total, page=page, page_size=page_size,
        items=[schemas.ProjectListOne.model_validate(i) for i in items]
    )


# ----------------------------------------------------------------------
# 项目详情
# ----------------------------------------------------------------------
async def get_project_detail_service(
    db: Session,
    project_id: int,
    user_id: int
) -> schemas.ProjectResponse:
    """
    获取项目详情，校验用户权限。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。
        user_id (int): 用户 ID。

    Returns:
        schemas.ProjectResponse: 项目详情响应。

    Raises:
        ItemNotFoundException: 项目不存在或无权限。
    """
    """
    Service: 获取项目详情，并检查用户权限。
    """
    db_obj = await crud_project.get(db, project_id)

    if not db_obj or db_obj.user_id != user_id:
        raise ItemNotFoundException("Project not found or access denied.")

    # 使用 ProjectResponse 包装
    return schemas.ProjectResponse(data=schemas.ProjectDetailOut.model_validate(db_obj))


# ==============================================================================
# 更新项目信息（无 AI）
# ==============================================================================
async def update_project_info_service(
    db: Session,
    project_id: int,
    user_id: int,
    update_data: Dict[str, Any]
) -> schemas.ProjectResponse:
    """
    更新项目基本信息（名称或描述），不涉及 AI 生成或 DDL 执行。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。
        user_id (int): 用户 ID。
        update_data (Dict[str, Any]): 更新字段。

    Returns:
        schemas.ProjectResponse: 更新后的项目详情响应。

    Raises:
        ItemNotFoundException: 项目不存在或无权限。
        OperationNotPermittedException: 项目已删除无法更新。
    """
    """
    修改名字或描述。
    注意：此函数完全不涉及 AI 生成或 DDL 执行，
    因此满足 '更改项目名字时候，不需要重新调用生成schema和ddl' 的需求。
    """
    db_obj = await crud_project.get(db, project_id)

    if not db_obj or db_obj.user_id != user_id:
        raise ItemNotFoundException("Project not found or access denied.")

    if db_obj.project_status == 'deleted':
        raise OperationNotPermittedException("Cannot update a deleted project.")

    # 仅执行普通的 CRUD update
    updated_obj = await crud_project.update(db, project_id, **update_data)

    return schemas.ProjectResponse(data=schemas.ProjectDetailOut.model_validate(updated_obj))



# --- 生成删除确认 Token ---
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


# --- 辅助函数 ---
async def _verify_delete_token(
    token: str,
    user_id: int,
    project_id: int,
) -> bool:
    try:
        # 直接使用 jwt.decode 获取完整 payload，而不是用 auth.decode_jwt_token
        payload = jwt.decode(
            token,
            config.jwt.secret_key,
            algorithms=[config.jwt.algorithm]
        )

        token_sub = payload.get("sub")
        token_pid = payload.get("project_id")

        # 1. 验证是否属于当前用户
        if str(token_sub) != str(user_id):
            return False

        # 2. 验证是否针对当前项目
        if token_pid is None or int(token_pid) != int(project_id):
            return False

        return True
    except (JWTError, ValueError, TypeError, AttributeError):
        # 任何解码错误或类型转换错误都视为验证失败
        return False


# --- 删除项目 ---
async def delete_project_service(
    db: Session, 
    project_id: int, 
    user_id: int, 
    confirmation_token: str
) -> bool:
    """
    执行项目删除操作，校验 Token 并释放用户额度。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。
        user_id (int): 用户 ID。
        confirmation_token (str): 删除确认 Token。

    Returns:
        bool: 删除操作是否成功。

    Raises:
        OperationNotPermittedException: Token 校验失败或项目已删除。
        ItemNotFoundException: 项目不存在。
    """
    if not await _verify_delete_token(confirmation_token, user_id, project_id):
        raise OperationNotPermittedException("Invalid token.")

    # [优化逻辑] 为了安全，再次确认项目状态，避免重复扣除额度
    project = await crud_project.get(db, project_id)
    if not project or project.project_status == 'deleted':
        # 如果已经是删除状态，直接返回 True，但不重复操作数据库
        return True

    # 执行软删除
    await crud_project.change_status(db, project_id, 'deleted')

    # [新增逻辑 3] 释放用户额度 (减 1)
    user = await crud_user_account.get(db, user_id)
    if user and user.used_databases > 0:
        await crud_user_account.update(
            db,
            user,
            used_databases=user.used_databases - 1
        )
    return True


# ==============================================================================
# 重新生成 Schema 的 ER 图
# ==============================================================================
async def regenerate_project_er_service(
        db: Session,
        project_id: int,
        user_id: int,
        schema_text: str,
        ai_model: str = "gpt4"
) -> schemas.ProjectResponse:
    """
    更新项目的 Schema 定义，并重新生成 Mermaid ER 代码。
    """
    # 1. 校验
    project = await crud_project.get(db, project_id)
    if not project or project.user_id != user_id:
        raise ItemNotFoundException("Project not found")

    # 2. 调用 AI 生成 (在线程池中运行同步代码)
    log.info(f"[RegenER] Regenerating ER for Project {project_id}...")
    loop = asyncio.get_event_loop()
    er_code = await loop.run_in_executor(
        None,
        AIService.generate_mermaid_code,
        schema_text,
        ai_model
    )

    # 3. 更新数据库
    current_def = project.schema_definition or {}
    current_def['schema'] = schema_text  # 更新 Schema

    project.schema_definition = current_def
    project.er_diagram_code = er_code  # 更新 Mermaid 代码

    # 可选：重置状态，提示用户 DDL 可能过期
    # project.creation_stage = schemas.CreationStageEnum.SCHEMA_GENERATED.value

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return schemas.ProjectResponse(data=schemas.ProjectDetailOut.model_validate(project))