import json
import httpx
import sqlparse
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_message import crud_message
from crud.crud_project import crud_project
from crud.crud_knowledge import crud_knowledge
from models.session import Session as SessionModel
from schema.chat import ChatResponse, MessageType
from core.log import log


# -----------------------
# AI 配置
# -----------------------
AI_SERVICE_URL = "http://26.64.77.145:1234/v1/chat/completions"
AI_MODEL = "codellama/CodeLlama-13b-Instruct-hf"
AI_API_KEY = "sk-YQjmNgkBJqRTsZCsr7r0zkHoLb6G0exL9u8gEkJTf5oZQXmE"


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
# 获取 Schema
# -----------------------
async def get_project_schema(db, project_id):
    project = await crud_project.get(db, project_id)

    if not project or not project.schema_definition:
        return "No schema defined."

    sd = project.schema_definition
    return json.dumps(sd, ensure_ascii=False, indent=2) if isinstance(sd, (dict, list)) else str(sd)


# -----------------------
# 获取术语库
# -----------------------
async def get_domain_knowledge(db, project_id):
    items = await crud_knowledge.get_by_project(db, project_id)

    if not items:
        return ""

    txt = "\n[业务术语]\n"
    for t in items:
        txt += f"- {t.term}: {t.definition}\n"

    return txt


# -----------------------
# 调用 Claude Agent
# -----------------------
async def call_ai_agent(schema, glossary, question):
    system_prompt = f"""
你是 SQL 专家，请根据 Schema 与 业务术语生成 SQL。

[Schema]
{schema}

[Domain Knowledge]
{glossary}

要求：
1. 必须返回 JSON
2. JSON 必须包含字段 "sql"
"""

    payload = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.1,
        "stream": False  # 添加 stream 参数
    }

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        log.info(f"Payload: {payload}")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(AI_SERVICE_URL, json=payload, headers=headers)


        resp.raise_for_status()
        raw = resp.json()

        log.info(f"Raw Response: {raw}")
        
        # 更健壮的响应解析
        if "choices" in raw and len(raw["choices"]) > 0:
            content = raw["choices"][0]["message"]["content"]
        else:
            # 尝试其他可能的响应格式
            content = raw.get("message", {}).get("content", "") or raw.get("content", "")
        
        # 清理内容
        clean = content.replace("```json", "").replace("```", "").strip()
        
        # 尝试解析 JSON
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            # 如果不是 JSON，返回原始内容
            return {"sql": clean}

    except Exception as e:
        print("AI Error:", e)
        return {"sql": f"-- AI Error: {str(e)}"}


# -----------------------
#   主流程（修改版）
# -----------------------
async def process_chat(db: AsyncSession, session_id: int, user_input: str, user_id: int):

    # 1. 存用户消息
    user_msg = await crud_message.create_message(
        db, session_id, user_input, role="user"
    )
    log.info(f"User message stored: {user_msg}")

    # 2. 获取上下文
    project_id = await get_project_id_by_session(db, session_id)
    schema = await get_project_schema(db, project_id)
    glossary = await get_domain_knowledge(db, project_id)
    log.info(f"Schema: {schema}")
    log.info(f"Glossary: {glossary}")

    # 3. 模型生成 SQL
    ai_json = await call_ai_agent(schema, glossary, user_input)
    sql_text = ai_json.get("sql", "-- no sql")

    # 4. SQL 类型判断
    try:
        parsed = sqlparse.parse(sql_text)
        sql_type = parsed[0].get_type().upper() if parsed else "UNKNOWN"
    except:
        sql_type = "UNKNOWN"

    # 5. 创建 AI 回复消息
    reply_content = f"生成 SQL 类型：{sql_type}"
    ai_message = await crud_message.create_message(
        db, session_id, reply_content, role="assistant"
    )

    # 6. 返回 AI 回复给前端
    return ChatResponse(
        message_id=ai_message.message_id,
        content=reply_content,  # AI 回复的文本内容
        message_type=MessageType.ASSISTANT,  # 标记为 AI 消息
        sql_text=sql_text,
        sql_type=sql_type,
        requires_confirmation=sql_type in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER"],
        data=None
    )