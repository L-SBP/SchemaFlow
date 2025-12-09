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
from service.mysql_service import create_mysql_user, sql_execute_in_mysql

# -----------------------
# AI 配置
# -----------------------
AI_SERVICE_URL = "http://1.92.127.206:8080/v1/chat/completions"
AI_MODEL = "codellama/CodeLlama-13b-Instruct-hf"
AI_API_KEY = "sk-2025texttosql"

# 【重要】Mock 开关
# True = 开启模拟模式（不联网，返回假数据，用于开发调试）
# False = 关闭模拟模式（尝试连接真实 AI）
MOCK_MODE = True


# -----------------------
# 工具：将 Schema JSON 转为日志里的文本格式
# -----------------------
def format_schema_to_text(schema_data):
    """
    将 JSON 对象转换为模型习惯的文本格式：
    Table: table_name, columns = [col1, col2, ...]
    """
    if not schema_data:
        return ""

    lines = []
    try:
        # 如果数据库里存的是字符串，先转成对象
        if isinstance(schema_data, str):
            schema_data = json.loads(schema_data)

        # 遍历表结构
        # 假设结构是: [{"table_name": "student", "columns": ["id", "name"]}]
        for table in schema_data:
            t_name = table.get("table_name", "unknown")
            cols = table.get("columns", [])

            # 容错处理：确保 cols 是列表
            if isinstance(cols, str):
                cols = [cols]

            # 构造日志里的核心格式
            col_str = ", ".join(str(c) for c in cols)
            line = f"Table: {t_name}, columns = [{col_str}]"
            lines.append(line)

        return "\n".join(lines)
    except Exception as e:
        log.error(f"Schema formatting error: {e}")
        # 如果解析失败，为了不报错，返回原始字符串
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
    user_prompt_content = f"""I want you to act as a SQL terminal in front of an database.
Here is the schema:
{schema_text}

I want you to answer the following question.
### Question: {question}

### Response:
"""

    # 修改此处：添加 "stop" 参数
    payload = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": "You are a SQL expert."},
            {"role": "user", "content": user_prompt_content}
        ],
        "temperature": 0.1,
        "stream": False,
        "stop": [";", "<|im_end|>"]  # <--- 新增：遇到分号或结束符立即停止
    }

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        log.info(f"Payload sending to AI: {payload}")

        # 建议：如果还是超时，可以尝试将 timeout 从 60 改为 120
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(AI_SERVICE_URL, json=payload, headers=headers)

        resp.raise_for_status()
        raw = resp.json()

        # =======================================================
        # 新增：打印 AI 返回的完整原始数据
        # =======================================================
        log.info(f"【AI Debug】Raw Response: {json.dumps(raw, ensure_ascii=False)}")

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

    # 获取转换成文本格式的 Schema (Change: 使用新函数)
    schema_text = await get_project_schema_text(db, project_id)

    # 3. 模型生成 SQL
    sql_text = await call_ai_agent(schema_text, user_input)

    if sql_text.startswith("-- Error calling AI:"):
        return ChatResponse(
            message_id=user_msg.message_id,
            content=sql_text,
            message_type=MessageType.ASSISTANT,
            sql_text=sql_text,
            sql_type="",
            requires_confirmation=False,
            data=None
        )

    # 4. SQL 类型判断
    sql_type = "UNKNOWN"
    try:
        if sql_text and not sql_text.startswith("--"):
            parsed = sqlparse.parse(sql_text)
            if parsed:
                sql_type = parsed[0].get_type().upper()
    except Exception as e:
        log.warning(f"SQL Parse warning: {e}")

    # 5. 执行 SQL
    sql_result = await sql_execute_in_mysql(db, project_id, sql_text, sql_type)
    log.info(f"SQL Result: {sql_result}")

    # 6. 创建 AI 回复消息
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