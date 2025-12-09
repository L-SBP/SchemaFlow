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

# ==========================================
# 新增：Schema 生成工具函数 (集成之前的逻辑)
# ==========================================
class SchemaGenerator:
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


# ==========================================
# 后台任务处理函数
# ==========================================
async def bg_generate_schema_task(project_id: int, requirements: str, db_name: str, db_type: str, ai_model: str):
    """
    后台任务：调用生成器，创建数据库，更新状态
    """
    log.info(f"[Task] Starting generation for Project {project_id} (DB: {db_type}, Model: {ai_model})...")

    # 1. 执行生成
    loop = asyncio.get_event_loop()
    schema_res, ddl_res = await loop.run_in_executor(
        None, SchemaGenerator.run_generation, requirements, db_name, db_type, ai_model
    )

    if not schema_res or not ddl_res:
        log.error(f"[Task] Generation failed for Project {project_id}")
        # 建议在此更新项目状态为 failed
        return

    log.info(f"[{ai_model}] Generated Schema Content:\n{schema_res}")
    log.info(f"[{ai_model}] Generated DDL Content:\n{ddl_res}")

    db_created = False

    try:
        # =================================================================
        # [修复] 获取 Root Engine 并使用同一个 Connection 执行所有操作
        # 避免连接池重置导致 USE database 失效
        # =================================================================
        root_engine = await MysqlHelper.get_root_engine()

        async with root_engine.connect() as conn:
            # 2.1 创建数据库
            log.info(f"[{db_type}] Creating Database: {db_name}")
            await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;"))
            db_created = True

            # 2.2 切换数据库上下文 (USE)
            log.info(f"[{db_type}] Switching context to: {db_name}")
            await conn.execute(text(f"USE `{db_name}`;"))

            # 2.3 执行表创建 DDL
            sorted_statements = sort_ddl_by_dependency(ddl_res, dialect=db_type)

            for stmt in sorted_statements:
                if not stmt.strip():
                    continue
                # 过滤掉 CREATE DATABASE
                if re.search(r'CREATE\s+DATABASE', stmt, re.IGNORECASE):
                    continue

                log.info(f"[{db_type}] Executing: {stmt[:50]}...")
                await conn.execute(text(stmt))

            # 提交事务
            await conn.commit()

        log.info(f"[{db_type}] Schema created successfully for {db_name}")

        # 3. 拼接完整 DDL 用于保存
        full_ddl_for_storage = f"CREATE DATABASE IF NOT EXISTS `{db_name}`;\nUSE `{db_name}`;\n\n{ddl_res}"

        # 4. 更新元数据 (PostgreSQL)
        async with PsqlHelper.get_session(PsqlHelper._get_async_engine(config.db)) as session:
            async with session.begin():
                project = await crud_project.get(session, project_id)
                instance = await crud_database_instance.get(session, project.instance_id)

                instance.db_name = db_name
                instance.status = "active"

                # 获取连接信息用于生成 URL (虽然这里没真正连接，但用于日志或返回)
                db_username = instance.db_username
                db_password = instance.db_password
                instance_host = instance.db_host
                instance_port = instance.db_port

                schema_definition_json = {
                    "schema": schema_res,
                    "ddl": full_ddl_for_storage
                }

                project.schema_definition = schema_definition_json
                project.project_status = 'active'

                session.add(instance)
                session.add(project)

        log.info(f"[PostgreSQL] Schema metadata updated for project {project_id}")

        # 可选：生成连接字符串记录日志 (修复了 URL 导入)
        # mysql_url = URL.create(
        #     drivername=config.mysql.driver,
        #     username=db_username,
        #     password=db_password,
        #     host=instance_host,
        #     port=instance_port,
        #     database=db_name
        # )
        # log.info(f"Connection URL generated: {mysql_url}")

    except Exception as e:
        log.error(f"[Task] Fatal error during schema creation: {str(e)}", exc_info=True)

        # 错误清理
        if db_created:
            try:
                cleanup_engine = await MysqlHelper.get_root_engine()
                async with cleanup_engine.connect() as conn:
                    await conn.execute(text(f"DROP DATABASE IF EXISTS `{db_name}`;"))
                    await conn.commit()
                log.info(f"[Cleanup] Dropped database {db_name} due to error")
            except Exception as cleanup_error:
                log.error(f"[Cleanup] Failed to drop database: {str(cleanup_error)}", exc_info=True)

    finally:
        temp_engine = PsqlHelper._get_async_engine(config.db)
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


# --- 1. 创建项目 ---
async def create_project_service(
        db: Session,
        project_in: schemas.ProjectCreate,
        user_id: int,
        background_tasks: BackgroundTasks
) -> schemas.ProjectAsyncResponse:
    """创建项目：先创建 DB 实例，再创建项目记录，最后调度异步任务"""
    try:
        # [新增逻辑 1] 检查用户额度
        user = await crud_user_account.get(db, user_id)
        if not user:
            raise ItemNotFoundException("User not found")

        # 检查是否超过最大数据库数量限制
        if user.used_databases >= user.max_databases:
            raise OperationNotPermittedException(
                f"Quota exceeded. You have used {user.used_databases}/{user.max_databases} databases."
            )
        project_data = project_in.model_dump()
        db_type = project_data.pop('db_type')

        # ==============================================================================
        # TODO: 后续考虑在项目中增加选用的模型这个字段
        # 修改：提取 ai_model，并在存入数据库前移除 (Project表中无此字段)
        # 默认值为 'gpt4'
        # ==============================================================================
        ai_model = project_data.pop('ai_model', 'gpt4')

        requirements_text = project_data.get('description', '')
        project_name = project_data.get('project_name', 'project')

        # 生成友好的 DB Name
        temp_db_name = generate_meaningful_db_name(project_name, user_id)

        # 1. 创建 DatabaseInstance
        new_instance = await crud_database_instance.create(
            db,
            db_type=db_type,
            db_host="127.0.0.1",
            db_port=3306,
            db_name="pending_init",
            db_username=f"test_{user_id}",
            db_password="User_secure_2025",
            status="inactive"
        )

        # 2. 创建 Project
        project_data['user_id'] = user_id
        project_data['instance_id'] = new_instance.instance_id
        project_data['project_status'] = 'initializing'

        db_obj = await crud_project.create(db, **project_data)

        # [新增逻辑 2] 增加用户已用额度
        await crud_user_account.update(
            db,
            user,
            used_databases=user.used_databases + 1
        )

        # 3. 调度异步任务
        # 核心修复：这里不再传递 db 参数
        background_tasks.add_task(
            bg_generate_schema_task,
            project_id=db_obj.project_id,
            requirements=requirements_text,
            db_name=temp_db_name,
            db_type=db_type,
            ai_model = ai_model
        )

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