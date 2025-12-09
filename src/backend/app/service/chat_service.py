import json
import httpx
import sqlparse
import asyncio
import random
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_message import crud_message
from crud.crud_project import crud_project
from crud.crud_database_instance import crud_database_instance
from models.session import Session as SessionModel
from mysql.mysql_database import MysqlHelper
from schema.chat import ChatResponse, MessageType
from core.log import log
from mysql.mysql_execute import execute_dql_user, execute_dml_user
from core.config import config
from core.exceptions import DatabaseOperationFailedException, SQLOperationFailedException
from service.mysql_service import create_mysql_user

# -----------------------
# AI 配置
# -----------------------
AI_SERVICE_URL = "http://26.64.77.145:1234/v1/chat/completions"
AI_MODEL = "codellama/CodeLlama-13b-Instruct-hf"
AI_API_KEY = "dummy-key"

# 【重要】Mock 开关
# True = 开启模拟模式（不联网，返回假数据，用于开发调试）
# False = 关闭模拟模式（尝试连接真实 AI）
MOCK_MODE = False


# 在 chat_service.py 中修改 format_schema_to_text 函数
def format_schema_to_text(schema_data):
    """
    将 JSON 对象转换为模型习惯的文本格式：
    Table: table_name, columns = [col1, col2, ...]
    """
    if not schema_data:
        return "No schema defined."

    lines = []
    try:
        # 如果 schema_data 已经是字符串但不是 JSON，直接返回
        if isinstance(schema_data, str):
            # 尝试解析 JSON
            try:
                parsed = json.loads(schema_data)
                schema_data = parsed
            except json.JSONDecodeError:
                # 如果不是 JSON 格式，直接返回原始字符串
                return schema_data

        # 处理不同的 schema 格式
        if isinstance(schema_data, list):
            # 格式 1: [{"table_name": "student", "columns": ["id", "name"]}]
            for item in schema_data:
                if isinstance(item, dict):
                    t_name = item.get("table_name", "unknown")
                    cols = item.get("columns", [])
                    if isinstance(cols, str):
                        cols = [cols]
                    col_str = ", ".join(str(c) for c in cols)
                    line = f"Table: {t_name}, columns = [{col_str}]"
                    lines.append(line)
                else:
                    # 如果是简单字符串列表，直接使用
                    lines.append(f"Table: {item}")

        elif isinstance(schema_data, dict):
            # 格式 2: {"tables": [...]} 或其他结构
            if "tables" in schema_data:
                for table in schema_data["tables"]:
                    t_name = table.get("table_name", "unknown")
                    cols = table.get("columns", [])
                    col_str = ", ".join(str(c) for c in cols)
                    line = f"Table: {t_name}, columns = [{col_str}]"
                    lines.append(line)
            else:
                # 尝试直接解析为表结构
                for key, value in schema_data.items():
                    if isinstance(value, list):
                        col_str = ", ".join(str(c) for c in value)
                        line = f"Table: {key}, columns = [{col_str}]"
                    else:
                        line = f"Table: {key}, value = {value}"
                    lines.append(line)

        return "\n".join(lines) if lines else "No schema defined."

    except Exception as e:
        log.error(f"Schema formatting error: {e}")
        # 返回原始数据
        return str(schema_data)

# -----------------------
# 获取 Session → Project
# -----------------------
async def get_project_id_by_session(db: AsyncSession, session_id: int) -> int:
    result = await db.execute(
        select(SessionModel).where(SessionModel.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")
    return session.project_id

# -----------------------
# 获取 Schema (已修改为返回特定文本格式)
# -----------------------
async def get_project_schema_text(db, project_id):
    project = await crud_project.get(db, project_id)
    if not project or not project.schema_definition:
        return "No schema defined."

    # 调用上面的工具函数进行转换
    return format_schema_to_text(project.schema_definition)

# -----------------------
# Mock 逻辑 (模拟 AI)
# -----------------------
async def mock_ai_response(question: str):
    """模拟 AI 的行为，根据关键词返回不同类型的 SQL"""
    log.info(f"【MOCK模式】正在模拟 AI 回复... 问题: {question}")
    
    # 模拟 1.5 秒网络延迟，让前端 Loading 转一会儿
    await asyncio.sleep(1.5)
    
    q = question.lower()
    
    # 根据问题包含的词，返回不同的 SQL，测试前端展示效果
    if "删除" in q or "delete" in q:
        return "DELETE FROM student WHERE id = 1001;"
    
    elif "修改" in q or "update" in q:
        return "UPDATE course SET credit = 4 WHERE name = 'Software Engineering';"
        
    elif "插入" in q or "添加" in q or "insert" in q:
        return "INSERT INTO student (id, name, age) VALUES (2024001, 'Test User', 20);"
        
    elif "平均" in q or "avg" in q:
        return "SELECT AVG(score) FROM exam_results WHERE course_id = 'SE101';"

    elif "帮我查一下最近的十个订单" in q or "count" in q:
        return """SELECT 
    BookingID,
    RoomType,
    StartDate AS 入住日期,
    EndDate AS 退房日期
FROM Booking
ORDER BY StartDate DESC
LIMIT 10; """
        
    else:
        # 默认查询
        return "SELECT * FROM student WHERE major = 'Software Engineering' LIMIT 10;"

# -----------------------
# 调用 AI Agent
# -----------------------
async def call_ai_agent(schema_text, question):
    
    # 1. 如果开启了 Mock 模式，直接拦截并返回
    if MOCK_MODE:
        return await mock_ai_response(question)

    # 2. 构造符合日志格式的 Prompt
    # 注意：这里严格遵循了 "Table: ..., columns = [...]" 和 "### Response:"
    user_prompt_content = f"""I want you to act as a SQL terminal in front of an database.
Here is the schema:
{schema_text}

I want you to answer the following question.
### Question: {question}

### Response:
"""

    payload = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": "You are a SQL expert."},
            {"role": "user", "content": user_prompt_content}
        ],
        "temperature": 0.1, 
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        log.info(f"Payload sending to AI: {payload}")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(AI_SERVICE_URL, json=payload, headers=headers)

        resp.raise_for_status()
        raw = resp.json()
        
        content = ""
        if "choices" in raw and len(raw["choices"]) > 0:
            content = raw["choices"][0]["message"]["content"]
        
        # 清理内容
        clean_sql = content.strip()
        if clean_sql.startswith("```sql"):
            clean_sql = clean_sql.replace("```sql", "").replace("```", "")
        
        return clean_sql.strip()

    except Exception as e:
        log.error(f"AI Connection Error: {e}")
        return f"-- Error calling AI: {str(e)}"

# -----------------------
#   主流程
# -----------------------
async def process_chat(db: AsyncSession, session_id: int, user_input: str, user_id: int):

    # 1. 存用户消息
    user_msg = await crud_message.create_message(
        db, session_id, user_input, role="user"
    )

    # 2. 获取上下文
    project_id = await get_project_id_by_session(db, session_id)
    
    # 获取项目信息和数据库实例
    project = await crud_project.get(db, project_id)
    instance = await crud_database_instance.get(db, project.instance_id)
    
    # 获取转换成文本格式的 Schema (Change: 使用新函数)
    schema_text = await get_project_schema_text(db, project_id)
    
    # 3. 模型生成 SQL 
    sql_text = await call_ai_agent(schema_text, user_input)
    log.info(f"SQL: {sql_text}")

    # 4. SQL 类型判断 与SQL 执行
    sql_type = "UNKNOWN"
    sql_result = None
    
    # 检查用户引擎是否存在
    if not MysqlHelper.is_user_engine_exists(instance.instance_id):
        # 检查用户是否已经创建
        if not MysqlHelper.check_user_exists(instance.instance_id):
            # 用户尚未创建，需要创建用户
            log.info(f"{instance.db_name}, {instance.db_username}, {instance.db_password}, {instance.user_database_url}, {instance.instance_id}")
            await create_mysql_user(instance.db_name, instance.db_username, instance.db_password, instance.user_database_url, instance.instance_id)
            log.info(f"[MySQL] User and engine created for instance {instance.instance_id}")
        else:
            # 用户已创建，但引擎未初始化，只需初始化引擎
            await MysqlHelper.init_user_engine(config.mysql, instance.instance_id, instance.user_database_url)
            log.info(f"[MySQL] User engine initialized for existing user in instance {instance.instance_id}")
    else:
        log.info(f"[MySQL] User engine already exists for instance {instance.instance_id}")

    try:
        if sql_text and not sql_text.startswith("--"):
            parsed = sqlparse.parse(sql_text)
            if parsed:
                sql_type = parsed[0].get_type().upper()
                
                # 如果是查询语句，执行并获取结果
                if sql_type == "SELECT":
                    sql_result = await execute_dql_user(sql_text, instance)
                # 如果是DML语句（INSERT/UPDATE/DELETE）
                elif sql_type in ["INSERT", "UPDATE", "DELETE"]:
                    await execute_dml_user(sql_text, instance)
    except Exception as e:
        log.error(f"Error executing {sql_type} query: {e}")
        raise SQLOperationFailedException(operation=sql_type, detail=str(e))

    # 5. 创建 AI 回复消息
    reply_content = f"已生成查询语句：\n{sql_text}"
    
    ai_message = await crud_message.create_message(
        db, session_id, reply_content, role="assistant"
    )

    # 6. 返回结果
    return ChatResponse(
        message_id=ai_message.message_id,
        content=reply_content, 
        message_type=MessageType.ASSISTANT,
        sql_text=sql_text,
        sql_type=sql_type,
        requires_confirmation=sql_type in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER"],
        data=sql_result
    )