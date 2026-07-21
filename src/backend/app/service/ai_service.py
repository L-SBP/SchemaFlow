# backend/app/service/ai_service.py

from core.llm import create_chat_model, get_model_for_task
from core.prompts.schema_prompt import SCHEMA_PROMPT
from core.prompts.ddl_prompt import DDL_PROMPT
from core.prompts.er_prompt import ER_PROMPT

class AIService:
    """
    项目 Schema 生成工具类。

    Methods:
        _parse_html_schema_only(html_content: str) -> str: 解析 HTML 获取 Schema。
        _request_ddl_remote(...): 远程调用 DDL 生成接口。
        run_generation(...): 执行 Schema 和 DDL 生成流程。
    """

    # --- Schema 生成逻辑 ---
    @staticmethod
    async def generate_schema(requirements, db_type, db_name, ai_model_hint=None):
        llm = (create_chat_model(ai_model_hint, temperature=0.1)
               if ai_model_hint
               else get_model_for_task("schema_generation"))
        chain = SCHEMA_PROMPT | llm
        response = await chain.ainvoke({
            "requirements": requirements, "db_type": db_type, "db_name": db_name,
        })
        return response.content

    @staticmethod
    async def generate_ddl(schema_text, requirements, db_type, db_name, ai_model_hint=None):
        llm = (create_chat_model(ai_model_hint, temperature=0.0)
               if ai_model_hint
               else get_model_for_task("ddl_generation"))
        chain = DDL_PROMPT | llm
        response = await chain.ainvoke({
            "schema_text": schema_text, "db_type": db_type, "db_name": db_name,
        })
        return _clean_ddl_output(response.content)

    # --- Mermaid ER 图生成逻辑 ---
    @staticmethod
    async def generate_mermaid_code(schema_text, ai_model_hint=None):
        llm = (create_chat_model(ai_model_hint, temperature=0.2)
               if ai_model_hint
               else get_model_for_task("er_generation"))
        chain = ER_PROMPT | llm
        response = await chain.ainvoke({"schema_text": schema_text})
        return _extract_mermaid_block(response.content)

def _clean_ddl_output(ddl_text: str) -> str:
    ddl_text = ddl_text.strip()
    if ddl_text.startswith("```sql"): ddl_text = ddl_text[6:]
    elif ddl_text.startswith("```"): ddl_text = ddl_text[3:]
    if ddl_text.endswith("```"): ddl_text = ddl_text[:-3]
    return ddl_text.strip()


def _extract_mermaid_block(er_text: str) -> str:
    import re
    match = re.search(r'```(?:mermaid)?\s*(.*?)\s*```', er_text, re.DOTALL)
    return match.group(1).strip() if match else er_text.strip()