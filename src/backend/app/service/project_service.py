# backend/app/service/project_service.py

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession as Session
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import BackgroundTasks  # <--- 新增导入
import requests
import json
import random
import string
import asyncio
from bs4 import BeautifulSoup

from core.sql_dialect_converter import SQLDialectConverter
from core.sql_sort import sort_ddl_by_dependency
# 隐式绝对导入
from crud.crud_project import crud_project
from crud.crud_database_instance import crud_database_instance
from crud.crud_user_account import crud_user_account
from mysql.mysql_converter import MySQLConverter
from mysql.mysql_execute import execute_sql_root
from mysql.mysql_converter import MySQLConverter
from mysql.mysql_execute import execute_sql_root
from schema import project as schemas
from core.exceptions import ItemNotFoundException, DatabaseOperationFailedException, OperationNotPermittedException, \
    ValidationException
from core.auth import decode_jwt_token, create_access_token
from core.config import config
from core.database import PsqlHelper
from mysql.mysql_database import MysqlHelper
from core.log import log
import re
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from sqlalchemy.engine import URL
from pypinyin import lazy_pinyin, Style  # <--- 1. 新增导入
from core.sql_sort import sort_ddl_by_dependency  # 确保导入了这个函数

# ==========================================
# 新增：Schema 生成工具函数 (集成之前的逻辑)
# ==========================================
class SchemaGenerator:
    """
    项目 Schema 生成工具类。

    Methods:
        _parse_html_schema_only(html_content: str) -> str: 解析 HTML 获取 Schema。
        _request_ddl_remote(...): 远程调用 DDL 生成接口。
        run_generation(...): 执行 Schema 和 DDL 生成流程。
    """
    BASE_HOST = "http://43.154.73.48:5000"
    DDL_API_URL = "https://schema2ddl.strangeloop.fun/generate/ddl"  # 新增 DDL 生成接口
    @staticmethod
    def _parse_html_schema_only(html_content: str) -> str:
        """
        仅解析 HTML 提取 Schema (Logical Design)，忽略 DDL
        """
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')

        # 1. 提取 Schema (Logical Design)
        schema_text = []
        # 使用模糊匹配找到 Logical Design 章节
        start_node = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3', 'h4'] and 'Logical Design' in tag.get_text())
        if start_node:
            current = start_node.find_next_sibling()
            while current:
                # 遇到下一个大标题就停止
                if current.name in ['h1', 'h2', 'h3', 'h4']:
                    break
                text = current.get_text(separator='\n', strip=True)
                if text:
                    schema_text.append(text)
                current = current.find_next_sibling()

        return "\n\n".join(schema_text)

    @classmethod
    def _request_ddl_remote(cls, schema_text: str, requirements: str, db_type: str, model: str = "gpt4") -> str:
        """
        步骤 2: 调用远程接口生成 DDL
        """
        payload = {
            "database_requirment": requirements,
            "schema": schema_text,
            "target_db_type": db_type,
            "model": model  # 暂定为 gpt4
        }

        try:
            # 设置超时时间
            resp = requests.post(cls.DDL_API_URL, json=payload, timeout=120)

            if resp.status_code == 200:
                res_json = resp.json()

                # =========================================================
                # 修改：根据新的 JSON 结构解析
                # 结构示例: {'validations': '...', 'ddl_statements': 'CREATE TABLE...'}
                # =========================================================
                ddl = res_json.get("ddl_statements", "")

                if not ddl:
                    print(f"[SchemaGen] Warning: 'ddl_statements' not found in response: {res_json}")

                return ddl
            else:
                print(f"[SchemaGen] DDL API failed: {resp.status_code} - {resp.text}")
                return ""
        except Exception as e:
            print(f"[SchemaGen] DDL API Exception: {e}")
            return ""

    @classmethod
    def run_generation(cls, requirements: str, db_name: str, db_type: str, ai_model: str = "gpt4"):
        """
        执行两步生成：
        1. Gradio -> 获取 Schema
        2. DDL API -> 获取 DDL
        Args:
            requirements (str): 项目需求描述。
            db_name (str): 目标数据库名称。
            db_type (str): 数据库类型（如 mysql、postgres）。
            ai_model (str, optional): 使用的 AI 模型，默认 'gpt4'。

        Returns:
            Tuple[str, str]: 包含生成的 Logical Design Schema 和 DDL。

        Raises:
            requests.RequestException: 网络请求失败。
            ValueError: 解析结果异常。
        """
        # --- 步骤 1: 获取 Schema (使用用户选择的 ai_model) ---
        session_hash = ''.join(random.choices(string.ascii_lowercase + string.digits, k=11))

        # Gradio Inputs: [Model, DB Name, Requirements, DBMS]
        inputs = [ai_model, db_name, requirements, db_type]
        headers = {"Content-Type": "application/json"}

        schema_res = ""

        try:
            # 1.1 提交任务
            resp = requests.post(
                f"{cls.BASE_HOST}/gradio_api/queue/join",
                json={"data": inputs, "session_hash": session_hash, "fn_index": 0},
                headers=headers, timeout=10
            )
            if resp.status_code != 200:
                print(f"[SchemaGen] Step 1 Submission failed: {resp.text}")
                return None, None

            # 1.2 监听结果
            resp = requests.get(
                f"{cls.BASE_HOST}/gradio_api/queue/data?session_hash={session_hash}",
                headers=headers, stream=True, timeout=120
            )

            for line in resp.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data: '):
                        try:
                            msg = json.loads(decoded[6:])
                            if msg.get('msg') == 'process_completed':
                                output_data = msg.get('output', {}).get('data', [])
                                if output_data:
                                    # 解析 HTML 获取 Schema
                                    schema_res = cls._parse_html_schema_only(output_data[0])
                        except:
                            continue
        except Exception as e:
            print(f"[SchemaGen] Step 1 Error: {e}")
            return None, None

        if not schema_res:
            print("[SchemaGen] Failed to retrieve schema from Step 1.")
            return None, None

        # --- 步骤 2: 获取 DDL (使用获得的 Schema + 暂定的 gpt4) ---
        print(f"[SchemaGen] Step 1 success. Schema length: {len(schema_res)}. Starting Step 2...")

        # 注意：第二个请求的 model 暂定为 gpt4
        ddl_res = cls._request_ddl_remote(schema_res, requirements, db_type, model="gpt4")

        return schema_res, ddl_res


# ==========================================
# 新增：生成有意义的数据库名称
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
# 1. 修改后台任务：只生成，不执行 (Generate Only Task)
# ==============================================================================
async def bg_generate_schema_only_task(project_id: int, requirements: str, db_name: str, db_type: str, ai_model: str):
    """
    后台任务：调用 SchemaGenerator 生成 Schema 和 DDL，并保存到数据库。

    Args:
        project_id (int): 项目 ID。
        requirements (str): 项目需求描述。
        db_name (str): 生成的数据库名称。
        db_type (str): 数据库类型（如 mysql）。
        ai_model (str): 使用的 AI 模型。

    Returns:
        None

    该任务不会直接执行建表，仅生成并保存 Schema/DDL。
    """
    """
    后台任务：调用生成器 -> 获取 Schema 和 DDL -> 存入数据库 JSON 字段 -> 结束。
    并不执行 CREATE TABLE。
    """
    log.info(f"[Task] Starting SCHEMA GENERATION ONLY for Project {project_id}...")

    # 1. 执行 AI 生成
    loop = asyncio.get_event_loop()
    schema_res, ddl_res = await loop.run_in_executor(
        None, SchemaGenerator.run_generation, requirements, db_name, db_type, ai_model
    )

    if not schema_res or not ddl_res:
        log.error(f"[Task] Generation failed for Project {project_id}")
        # 这里可以更新状态为 error，或者保留 initializing 让用户重试
        return

    # =========================================================
    # [修复 1] 恢复日志打印，方便调试查看 AI 生成结果
    # =========================================================
    log.info(f"[{ai_model}] Generated Schema Content:\n{schema_res}")
    log.info(f"[{ai_model}] Generated DDL Content:\n{ddl_res}")

    log.info(f"[{ai_model}] Generated content ready. Saving to DB for confirmation...")

    # 2. 存入 PostgreSQL 的 project.schema_definition 字段
    # 使用独立的 Session，因为这是后台任务
    temp_engine = PsqlHelper._get_async_engine(config.db)
    async with PsqlHelper.get_session(temp_engine) as session:
        async with session.begin():
            project = await crud_project.get(session, project_id)
            if project:
                # =========================================================
                # [修复 2] 拼接完整的 CREATE DATABASE 和 USE 语句
                # 替代之前的 -- 注释，避免 deploy 时正则匹配失败导致第一张表被跳过
                # =========================================================
                full_ddl_preview = f"CREATE DATABASE IF NOT EXISTS `{db_name}`;\nUSE `{db_name}`;\n\n{ddl_res}"

                schema_data = {
                    "schema": schema_res,
                    "ddl": full_ddl_preview,
                    "generated_db_name": db_name  # 暂存生成的库名
                }

                project.schema_definition = schema_data
                # 状态保持 initializing，或者设为 pending_confirmation
                # 只要前端判断 schema_definition 有值且 status != active 即可进入确认页
                project.project_status = 'initializing'

                session.add(project)
                log.info(f"[Task] Schema saved for Project {project_id}. Waiting for user confirmation.")

    await temp_engine.dispose()



# --- 辅助函数 ---
async def _verify_delete_token(token: str, user_id: int, project_id: int) -> bool:
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


# ==============================================================================
# 2. 修改 Create Service：调用新的“只生成”任务
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
    db_type = project_data.pop('db_type')
    ai_model = project_data.pop('ai_model', 'gpt4')
    requirements_text = project_data.get('description', '')
    project_name = project_data.get('project_name', 'project')

    # 生成 DB Name，但不创建物理库
    temp_db_name = generate_meaningful_db_name(project_name, user_id)

    # 1. 创建 DatabaseInstance (占位)
    new_instance = await crud_database_instance.create(
        db,
        db_type=db_type,
        db_host="127.0.0.1",
        db_port=3306,
        db_name=temp_db_name,  # 此时物理库还未创建
        db_username=f"test_{user_id}",
        db_password="User_secure_2025",
        status="inactive"  # 还没真正激活
    )

    # 2. 创建 Project
    project_data['user_id'] = user_id
    project_data['instance_id'] = new_instance.instance_id
    project_data['project_status'] = 'initializing'

    db_obj = await crud_project.create(db, **project_data)

    # 3. 调度“只生成”任务
    background_tasks.add_task(
        bg_generate_schema_only_task,  # <--- 替换为新任务
        project_id=db_obj.project_id,
        requirements=requirements_text,
        db_name=temp_db_name,
        db_type=db_type,
        ai_model=ai_model
    )

    # 更新配额 (虽然还没最终建库，但占用了生成资源，先预扣)
    await crud_user_account.update(db, user, used_databases=user.used_databases + 1)

    return schemas.ProjectAsyncResponse.model_validate(db_obj)

# --- 2. 获取列表 ---
async def get_projects_list_service(
        db: Session, user_id: int, search: Optional[str], page: int, page_size: int
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


# ==============================================================================
# 3. 新增 Service：执行部署 (Execute DDL)
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
    # 1. 校验项目
    project = await crud_project.get(db, project_id)
    if not project or project.user_id != user_id:
        raise ItemNotFoundException("Project not found")

    # 获取关联的 Instance 信息
    instance = await crud_database_instance.get(db, project.instance_id)
    db_name = instance.db_name
    db_type = instance.db_type  # e.g. 'mysql'

    # 获取 DDL
    final_ddl = deploy_data.confirmed_ddl

    # 2. 准备执行语句列表
    execution_statements = []

    try:
        # =============================================================
        # 预留接口逻辑：根据 use_smart_parse 决定处理方式
        # =============================================================
        if deploy_data.use_smart_parse:
            log.info(f"[Deploy] Smart Parse ENABLED for Project {project_id}. Running cleanup & sort.")

            # 步骤 A: 清洗 DDL (去除 -- 注释，防止干扰解析器)
            lines = final_ddl.splitlines()
            cleaned_lines = [line for line in lines if not line.strip().startswith('--')]
            cleaned_ddl = "\n".join(cleaned_lines)

            # 步骤 B: 调用方言转换和拓扑排序
            # sort_ddl_by_dependency 内部使用了 sqlglot，会自动处理方言转换并按依赖排序
            try:
                execution_statements = sort_ddl_by_dependency(cleaned_ddl, dialect=db_type)
            except Exception as sort_err:
                log.error(f"[Deploy] Smart Parse failed: {sort_err}")
                raise ValidationException(f"SQL解析或排序失败: {str(sort_err)}。请检查DDL语法。")

        else:
            log.info(f"[Deploy] Smart Parse DISABLED for Project {project_id}. Running raw execution.")
            # 简单分割，不做任何排序和转换 (适用于未来 DDL 已经完美的情况)
            execution_statements = [s.strip() for s in final_ddl.split(';') if s.strip()]

    except Exception as e:
        raise ValidationException(f"DDL Pre-processing failed: {str(e)}")

    # 3. 执行物理建库操作
    log.info(f"[Deploy] Starting deployment for Project {project_id}, DB: {db_name}")

    try:
        root_engine = await MysqlHelper.get_root_engine()

        async with root_engine.connect() as conn:
            # 3.1 重置数据库 (Drop & Create) - 确保环境干净
            log.info(f"[{db_type}] Resetting Database: {db_name}")
            await conn.execute(text(f"DROP DATABASE IF EXISTS `{db_name}`;"))
            await conn.execute(text(f"CREATE DATABASE `{db_name}`;"))

            # 3.2 切换上下文
            await conn.execute(text(f"USE `{db_name}`;"))

            # 3.3 执行语句
            for stmt in execution_statements:
                if not stmt.strip():
                    continue

                # 过滤掉 CREATE DATABASE (因为我们已经在 3.1 手动执行了)
                if re.search(r'CREATE\s+DATABASE', stmt, re.IGNORECASE):
                    continue

                # 过滤掉 USE 语句 (避免上下文切换冲突)
                if re.match(r'^\s*USE\s+', stmt, re.IGNORECASE):
                    continue

                log.info(f"[{db_type}] Executing: {stmt[:60]}...")
                await conn.execute(text(stmt))

            await conn.commit()

        # 4. 更新项目状态为 Active
        current_schema_def = project.schema_definition or {}
        current_schema_def['ddl'] = final_ddl
        if deploy_data.confirmed_schema:
            current_schema_def['schema'] = deploy_data.confirmed_schema

        await crud_project.update(
            db,
            project_id,
            project_status='active',
            schema_definition=current_schema_def
        )

        # 更新 Instance 状态
        await crud_database_instance.update(db, instance, status='active')

        log.info(f"[Deploy] Project {project_id} deployed successfully.")

        # 重新获取最新数据返回
        refreshed_project = await crud_project.get(db, project_id)
        return schemas.ProjectResponse(data=schemas.ProjectDetailOut.model_validate(refreshed_project))

    except Exception as e:
        log.error(f"[Deploy] Database Execution Error: {e}", exc_info=True)
        # 抛出异常，前端提示部署失败
        raise DatabaseOperationFailedException(f"Deployment failed during execution: {str(e)}")




# ----------------------------------------------------------------------
# 3. GET Project Detail
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

    # <--- 修正点 2：使用 ProjectResponse 包装
    return schemas.ProjectResponse(data=schemas.ProjectDetailOut.model_validate(db_obj))


# ==============================================================================
# 4. 确认 Update Service 不包含 AI 逻辑
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



# --- 5. 确认删除 (生成Token) ---
async def confirm_delete_project_service(
        db: Session, project_id: int, user_id: int, confirmation_text: str
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


# --- 6. 最终删除 ---
async def delete_project_service(
        db: Session, project_id: int, user_id: int, confirmation_token: str
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