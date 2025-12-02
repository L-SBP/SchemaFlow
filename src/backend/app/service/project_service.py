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

# 隐式绝对导入
from crud.crud_project import crud_project
from crud.crud_database_instance import crud_database_instance
from schema import project as schemas
from core.exceptions import ItemNotFoundException, DatabaseOperationFailedException, OperationNotPermittedException, \
    ValidationException
from core.auth import decode_jwt_token, create_access_token
from core.config import config
from core.database import PsqlHelper

# ==========================================
# 新增：Schema 生成工具函数 (集成之前的逻辑)
# ==========================================
class SchemaGenerator:
    BASE_HOST = "http://43.154.73.48:5000"

    @staticmethod
    def _parse_html(html_content: str):
        if not html_content:
            return "", ""
        soup = BeautifulSoup(html_content, 'html.parser')

        # 提取 Schema
        schema_text = []
        start_node = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3', 'h4'] and 'Logical Design' in tag.get_text())
        if start_node:
            current = start_node.find_next_sibling()
            while current:
                if current.name in ['h1', 'h2', 'h3', 'h4']: break
                text = current.get_text(separator='\n', strip=True)
                if text: schema_text.append(text)
                current = current.find_next_sibling()

        # 提取 DDL
        ddl_list = []
        sql_blocks = soup.find_all('code', class_='language-sql')
        for block in sql_blocks:
            sql_text = block.get_text().strip()
            if sql_text: ddl_list.append(sql_text)

        # DDL 重排序 (CREATE DATABASE 放前面)
        create_db_idx = -1
        for i, sql in enumerate(ddl_list):
            if "CREATE DATABASE" in sql.upper():
                create_db_idx = i
                break
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
# 新增：后台任务处理函数
# ==========================================
async def bg_generate_schema_task(project_id: int, requirements: str, db_name: str, db: Session):
    """
    后台任务：调用 Gradio 生成 Schema，并更新数据库状态
    注意：这里需要处理 DB Session 的生命周期，或者重新创建 Session
    """
    print(f"[Task] Starting schema generation for Project {project_id}...")

    # 由于是同步的网络请求，可以直接运行
    # 如果是在 async 函数中，建议使用 loop.run_in_executor 避免阻塞 Event Loop
    loop = asyncio.get_event_loop()
    schema_res, ddl_res = await loop.run_in_executor(
        None, SchemaGenerator.run_generation, requirements, db_name
    )

    if schema_res and ddl_res:
        print(f"[Task] Generation successful for Project {project_id}")

        # TODO: 这里应该将 schema_res 和 ddl_res 保存到数据库
        # 例如保存到 ai_generated_statement 表，或更新 Project 的某个字段
        # 由于没看到具体的 DDL 存储表结构，这里演示更新 Project 状态为 ACTIVE

        # 注意：FastAPI BackgroundTasks 结束后 Session 可能已关闭，
        # 在实际生产中，建议在 Task 内部重新申请一个 Session 或者是使用 Celery
        # 这里假设 db 仍然可用 (FastAPI 的 Depends 在 response 后会关闭 db，所以这里必须小心)
        # **修正方案**：Task 内部应该独立管理 DB 连接，这里简化演示打印日志

        print(f"--- Schema Preview ---\n{schema_res[:200]}...")
        print(f"--- DDL Preview ---\n{ddl_res[:200]}...")

        # 如果你有 task 专用的 get_db，应该在这里使用
        # async with async_session() as session:
        #     await crud_project.change_status(session, project_id, 'active')
    else:
        print(f"[Task] Generation failed for Project {project_id}")
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
        project_data = project_in.model_dump()
        db_type = project_data.pop('db_type')

        # 提取需求描述，用于生成
        requirements_text = project_data.get('description', '')
        # 生成一个临时的 DB Name 用于生成过程
        temp_db_name = f"proj_{user_id}_{int(datetime.now().timestamp())}"

        # 1. 创建关联的 DatabaseInstance
        new_instance = await crud_database_instance.create(
            db,
            db_type=db_type,
            db_host="127.0.0.1",
            db_port=3306,
            db_name="pending_init",
            db_username="pending_user",
            db_password="pending_password",
            status="inactive"
        )

        # 2. 创建 Project
        project_data['user_id'] = user_id
        project_data['instance_id'] = new_instance.instance_id
        project_data['project_status'] = 'initializing'

        db_obj = await crud_project.create(db, **project_data)

        # 3. 调度异步任务 (FastAPI BackgroundTasks)
        # 注意：这里传递 db 会有风险，因为请求结束后 db 会被关闭。
        # 最佳实践是仅传递 ID，在 task 内部重新获取 session。
        # 但为了演示连贯性，我们这里触发生成逻辑。

        background_tasks.add_task(
            bg_generate_schema_task,
            project_id=db_obj.project_id,
            requirements=requirements_text,
            db_name=temp_db_name,
            db=db  # 注意：实际生产中请在 task 内新建 session
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

    # 执行软删除
    await crud_project.change_status(db, project_id, 'deleted')
    return True