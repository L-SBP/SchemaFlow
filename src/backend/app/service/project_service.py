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
from pypinyin import lazy_pinyin, Style  # <--- 1. 新增导入

# ==========================================
# 新增：Schema 生成工具函数 (集成之前的逻辑)
# ==========================================
class SchemaGenerator:
    BASE_HOST = "http://43.154.73.48:5000"

    @staticmethod
    def _parse_html(html_content: str):
        """
        解析 HTML 提取 Schema 和 DDL
        修复：增加了 SQL 语句去重逻辑，防止 Appendix 章节导致代码重复
        """
        if not html_content:
            return "", ""
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

        # 2. 提取 DDL (核心修复：去重)
        ddl_list = []
        seen_sql = set()  # <--- 用于记录已经添加过的 SQL 内容

        sql_blocks = soup.find_all('code', class_='language-sql')

        for block in sql_blocks:
            sql_text = block.get_text().strip()

            # 只有非空且【未出现过】的 SQL 块才添加
            if sql_text and sql_text not in seen_sql:
                ddl_list.append(sql_text)
                seen_sql.add(sql_text)  # <--- 标记为已添加

        # 3. DDL 重排序 (确保 CREATE DATABASE 放最前面)
        create_db_idx = -1
        for i, sql in enumerate(ddl_list):
            if "CREATE DATABASE" in sql.upper():
                create_db_idx = i
                break

        # 如果找到了 CREATE DATABASE 且不在第一位，把它挪到第一位
        if create_db_idx > 0:
            ddl_list.insert(0, ddl_list.pop(create_db_idx))

        return "\n\n".join(schema_text), "\n\n".join(ddl_list)

    @classmethod
    def run_generation(cls, requirements: str, db_name: str, db_type: str = "MySQL"):
        session_hash = ''.join(random.choices(string.ascii_lowercase + string.digits, k=11))
        # 注意顺序：1.Model, 2.DB Name, 3.Requirements , 4.DBMS
        inputs = ["gpt4", db_name, requirements, db_type]

        headers = {"Content-Type": "application/json"}

        try:
            # 1. 提交任务
            resp = requests.post(
                f"{cls.BASE_HOST}/gradio_api/queue/join",
                json={"data": inputs, "session_hash": session_hash, "fn_index": 0},
                headers=headers, timeout=10
            )
            if resp.status_code != 200:
                print(f"[SchemaGen] Submission failed: {resp.text}")
                return None, None

            # 2. 监听结果 (使用 requests stream, 阻塞式但运行在后台线程)
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
                                    return cls._parse_html(output_data[0])
                        except:
                            continue
        except Exception as e:
            print(f"[SchemaGen] Error: {e}")
            return None, None
        return None, None


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
# 新增：后台任务处理函数
# ==========================================
async def bg_generate_schema_task(project_id: int, requirements: str, db_name: str):
    """
    后台任务：调用 Gradio 生成 Schema，并更新数据库状态
    """
    print(f"[Task] Starting schema generation for Project {project_id}...")

    # 1. 执行生成 (这是一个耗时的同步 IO 操作，使用 executor 运行)
    loop = asyncio.get_event_loop()
    schema_res, ddl_res = await loop.run_in_executor(
        None, SchemaGenerator.run_generation, requirements, db_name
    )

    # # 模拟生成结果
    # schema_res = "test"
    # ddl_res = """CREATE DATABASE ce_shi_xiang_mu_1_oaz9;
    #
    # CREATE TABLE Hotel (Name TEXT NOT NULL, Address TEXT, Phone TEXT, PRIMARY KEY(Name));
    #
    # CREATE TABLE Room (Type TEXT NOT NULL, Price NUMERIC, Quantity NUMERIC, PRIMARY KEY(Type));
    #
    # CREATE TABLE Booking (BookingID TEXT NOT NULL, RoomType TEXT NOT NULL, StartDate DATETIME, EndDate DATETIME, PRIMARY KEY(BookingID), FOREIGN KEY(RoomType) REFERENCES Room(Type));
    #
    # CREATE TABLE User (UserID TEXT NOT NULL, Name TEXT, Contact TEXT, Discount NUMERIC, CreditCard TEXT, PRIMARY KEY(UserID));
    #
    # CREATE TABLE Booking_Room (BookingID TEXT NOT NULL, RoomType TEXT NOT NULL, Duration NUMERIC, RoomPreference TEXT, PRIMARY KEY(BookingID, RoomType), FOREIGN KEY(BookingID) REFERENCES Booking(BookingID), FOREIGN KEY(RoomType) REFERENCES Room(Type));
    #
    # CREATE TABLE User_Booking (UserID TEXT NOT NULL, BookingID TEXT NOT NULL, PaymentMethod TEXT, LoyaltyProgram TEXT, PRIMARY KEY(UserID, BookingID), FOREIGN KEY(UserID) REFERENCES User(UserID), FOREIGN KEY(BookingID) REFERENCES Booking(BookingID));"""


    db_name_extracted = None

    try:
        # 1. 执行DDL（创建数据库和表）
        create_db_match = re.search(r'CREATE\s+DATABASE\s+`?(\w+)`?', ddl_res, re.IGNORECASE)
        if not create_db_match:
            raise ValueError("Invalid CREATE DATABASE statement")
        db_name_extracted = create_db_match.group(1)

        # 执行数据库创建
        await execute_sql_root(f"CREATE DATABASE IF NOT EXISTS `{db_name_extracted}`;")
        await execute_sql_root(f"USE `{db_name_extracted}`;")

        # 执行表创建
        sorted_statements = sort_ddl_by_dependency(ddl_res, dialect="mysql")
        for stmt in sorted_statements:
            if not stmt.strip() or re.search(r'CREATE\s+DATABASE', stmt, re.IGNORECASE):
                continue
            log.info(f"[MySQL] Executing: {stmt}")
            await execute_sql_root(f"{stmt};")

        log.info(f"[MySQL] Schema created successfully for {db_name_extracted}")

        # 2. 更新元数据
        async with PsqlHelper.get_session(PsqlHelper._get_async_engine(config.db)) as session:
            async with session.begin():
                project = await crud_project.get(session, project_id)
                instance = await crud_database_instance.get(session, project.instance_id)

                # 直接更新实例对象属性
                instance.db_name = db_name_extracted
                instance.status = "active"

                # 获取用户名和密码
                db_username = instance.db_username
                db_password = instance.db_password
                instance_id = instance.instance_id

                # 更新项目
                schema_definition_json = {
                    "schema": schema_res,
                    "ddl": ddl_res
                }

                project.schema_definition = schema_definition_json
                project.project_status = 'active'

                # 提交所有更改
                session.add(instance)
                session.add(project)

        log.info(f"[PostgreSQL] Schema metadata updated for project {project_id}")

        # 3. 创建MySQL连接URL
        # 注意：使用正确的驱动配置，假设 config.mysql.driver 是 'mysql+pymysql'
        mysql_url = URL.create(
            drivername=config.mysql.driver,
            username=db_username,
            password=db_password,
            host=instance.db_host,
            port=instance.db_port,
            database=db_name_extracted
        )

        log.info(f"[Task] Schema generation completed, user creation queued for project {project_id}")

    except Exception as e:
        log.error(f"[Task] Fatal error during schema creation: {str(e)}", exc_info=True)

        # 清理：删除已创建的数据库
        if db_name_extracted:
            try:
                await execute_sql_root(f"DROP DATABASE IF EXISTS `{db_name_extracted}`;")
                log.info(f"[Cleanup] Dropped database {db_name_extracted} due to error")
            except Exception as cleanup_error:
                log.error(f"[Cleanup] Failed to drop database: {str(cleanup_error)}", exc_info=True)

        # 更新项目状态为错误
        # await _set_project_status(project_id, 'error')

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
            db_name=temp_db_name
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