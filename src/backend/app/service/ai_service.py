# backend/app/service/ai_service.py
import requests
import json
import random
import string
from bs4 import BeautifulSoup
from openai import OpenAI
from core.log import log
from core.config import settings

class AIService:
    """
    项目 Schema 生成工具类。

    Methods:
        _parse_html_schema_only(html_content: str) -> str: 解析 HTML 获取 Schema。
        _request_ddl_remote(...): 远程调用 DDL 生成接口。
        run_generation(...): 执行 Schema 和 DDL 生成流程。
    """
    BASE_HOST = "http://43.154.73.48:5000"
    DDL_API_URL = "https://schema2ddl.strangeloop.fun/generate/ddl"

    # --- Schema 生成逻辑 ---
    @classmethod
    def generate_schema(cls, requirements: str, db_name: str, db_type: str, ai_model: str = "gpt4") -> str:
        """
        仅生成 Schema (Logical Design)
        """
        session_hash = ''.join(random.choices(string.ascii_lowercase + string.digits, k=11))
        inputs = [ai_model, db_name, requirements, db_type]
        headers = {"Content-Type": "application/json"}
        schema_res = ""

        try:
            resp = requests.post(
                f"{cls.BASE_HOST}/gradio_api/queue/join",
                json={"data": inputs, "session_hash": session_hash, "fn_index": 0},
                headers=headers, timeout=10
            )
            if resp.status_code != 200:
                log.error(f"[SchemaGen] Step 1 Submission failed: {resp.text}")
                return ""

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
                                    schema_res = cls._parse_html_schema_only(output_data[0])
                        except:
                            continue
            return schema_res
        except Exception as e:
            log.error(f"[SchemaGen] Step 1 Error: {e}")
            return ""

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

    # --- DDL 生成逻辑 ---
    @classmethod
    def generate_ddl(cls, schema_text: str, requirements: str, db_type: str, ai_model: str = "gpt4") -> str:
        """
        根据 Schema 和需求生成 DDL
        """
        payload = {
            "database_requirment": requirements,
            "schema": schema_text,
            "target_db_type": db_type,
            "model": ai_model
        }
        try:
            resp = requests.post(cls.DDL_API_URL, json=payload, timeout=120)
            if resp.status_code == 200:
                res_json = resp.json()
                return res_json.get("ddl_statements", "")
            else:
                log.error(f"[SchemaGen] DDL API failed: {resp.status_code} - {resp.text}")
                return ""
        except Exception as e:
            log.error(f"[SchemaGen] DDL API Exception: {e}")
            return ""

    # --- Mermaid ER 图生成逻辑 ---
    @classmethod
    def generate_mermaid_code(cls,schema_text: str, ai_model: str = "gpt4") -> str:
        # 1. API Key 配置
        # TODO:后续不能写死
        api_key = settings.ai.mermaid_api_key
        base_url = "https://ai.nengyongai.cn/v1"

        if not api_key:
            log.warning("[ERGen] No API Key found.")
            return ""

        # 2. 模型映射 (新增)
        model_mapping = {
            'gpt4': 'gpt-4o-2024-08-06',
            'chatgpt': 'gpt-3.5-turbo',
            'qwen': 'Qwen/Qwen3-32B',
            'deepseek': 'deepseek-v3-241226'
        }
        real_model = model_mapping.get(ai_model, 'gpt-4o-2024-08-06')

        try:
            client = OpenAI(api_key=api_key, base_url=base_url)

            # 3. 使用新的 Prompt (更新)
            prompt = """You are a professional database designer.

    Given the following Entity Sets and Relationship Sets, please generate a complete and accurate Mermaid ER diagram code using `erDiagram` syntax. Follow these strict rules:

    1. Use `PK` and `FK` to mark primary and foreign keys in the entity or relationship tables.
    2. Use `||--o{`, `||--||`, `o{--o{` etc. to represent correct cardinality:
       - `||--o{` means one-to-many
       - `||--||` means one-to-one
       - `o{--o{` means many-to-many
    3. For relationship sets, if needed, create a separate entity-like table to store relationship attributes and foreign keys.
    4. Do not include any extra explanation or markdown syntax like ```mermaid. Just return the raw ER diagram code.
    5. Use appropriate attribute types like `int`, `string`, `date`, `float`, etc., based on the names.
    6. **Attribute Order (CRITICAL)**: 
       - You MUST follow the format: `Type Name Key`.
       - The Key (PK/FK) must ALWAYS be at the **end** of the line.
       - **Correct**: `string StudentID PK`
       - **WRONG**: `string PK StudentID` (Never put PK/FK before the name)

    7. **Composite Keys (CRITICAL)**: 
       - If an attribute is **BOTH** a Primary Key and a Foreign Key, you MUST separate them with a **COMMA**.
       - **Correct**: `string course_id PK, FK`
       - **WRONG**: `string course_id PK FK` (Missing comma causes error)
        """

            response = client.chat.completions.create(
                model=real_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt + "\n\nRequirement:\n" + schema_text
                    }
                ],
                temperature=0.1
            )

            content = response.choices[0].message.content
            content = content.replace("```mermaid", "").replace("```", "").strip()

            # 4. 拼接主题 (新增)
            theme_config = {
                "theme": "base",
                "themeVariables": {
                    "primaryColor": "#ffffff",
                    "primaryTextColor": "#000000",
                    "primaryBorderColor": "#3370ff",
                    "lineColor": "#3370ff",
                    "tertiaryColor": "#e6f7ff",
                    "tertiaryBorderColor": "#3370ff",
                    "tertiaryTextColor": "#000000",
                    "mainBkg": "#ffffff",
                    "edgeLabelBackground": "#fff"
                }
            }
            init_directive = f"%%{{init: {json.dumps(theme_config)} }}%%\n"

            return init_directive + content

        except Exception as e:
            log.error(f"[ERGen] Error generating mermaid code: {e}")
            return ""