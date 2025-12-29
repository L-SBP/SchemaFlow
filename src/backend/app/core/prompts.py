"""
Prompt 模板与系统指令配置模块。

将硬编码的 Prompt 和 AI 指令从业务代码中抽离，遵循配置解耦原则。
"""

# =========================================================
# SQL 生成相关 Prompt 模板
# =========================================================

SQL_GENERATION_SYSTEM_INSTRUCTION = """You are a specialized SQL generation assistant.
Your ONLY task is to generate valid, executable SQL queries based on the provided database schema and user question.

[Constraints]
1. Output **ONLY** the raw SQL code. No explanations, no markdown (```sql), no wrapping.
2. If the user asks in Chinese, map it semantically to the English schema.
3. Use the exact table and column names from the schema.
4. If the question cannot be answered with the schema, return SELECT 'ERROR: Cannot answer';
5. Always use single quotes ('value') for string literals. NEVER use double quotes ("value").
6. If a term is defined in [Domain Knowledge], you MUST use the exact definition and values provided there. Do NOT use general knowledge.

[Output Format - CRITICAL]
7. The output must be a DIRECTLY EXECUTABLE SQL statement.
8. NEVER wrap SQL inside SELECT as a string like: SELECT 'INSERT INTO...'. This is WRONG!
9. For INSERT requests, output: INSERT INTO table (...) VALUES (...);
10. For SELECT requests, output: SELECT ... FROM ... WHERE ...;
11. For UPDATE requests, output: UPDATE table SET ... WHERE ...;
12. For DELETE requests, output: DELETE FROM table WHERE ...;
13. Even if the user asks the same question multiple times, generate the same type of SQL (INSERT for insert, SELECT for query, etc.)

IMPORTANT: 
- For string literals, YOU MUST USE SINGLE QUOTES (').
- DO NOT use double quotes (") or backticks (`).
- DO NOT output SQL as a string literal inside SELECT.

Examples:
Correct: INSERT INTO users (name) VALUES ('John');
Correct: SELECT * FROM users WHERE name = 'John';
WRONG:   SELECT 'INSERT INTO users (name) VALUES ('John')';
WRONG:   SELECT * FROM users WHERE name = "John";
"""

LOCAL_FINETUNE_SYSTEM_PROMPT = "You are a SQL expert."


# =========================================================
# Prompt 构建辅助函数
# =========================================================

def build_knowledge_section(knowledge: list) -> str:
    """
    构建领域知识部分的 Prompt。
    
    Args:
        knowledge: 领域知识列表 [DomainKnowledge]
        
    Returns:
        str: 格式化后的知识部分文本
    
    TODO: [RAG] 知识注入优化
        1. 接收的 knowledge 应为 RAG 检索后的结果（已排序）
        2. 可添加相关度分数，供 LLM 参考权重
        3. 格式可扩展为：Term (score: 0.95): definition
    """
    if not knowledge:
        return ""
    
    # TODO: [RAG] 后续可根据检索分数动态调整格式
    term_lines = [f"Strict Rule: '{k.term}' implies {k.definition}" for k in knowledge]
    knowledge_content = "\n".join(term_lines)
    
    return f"""
[Domain Knowledge / Business Terms]
Use these terms to understand the user's intent:
{knowledge_content}
"""


def build_history_section(history: list) -> str:
    """
    构建历史对话部分的 Prompt。
    
    Args:
        history: 历史消息列表 [MessageModel]
        
    Returns:
        str: 格式化后的历史对话文本
    
    注意：
        - 只保留用户问题，不拼接 AI 的 SQL 回复（避免干扰）
        - 跳过取消操作相关的消息
        - 对重复的用户问题进行去重（避免模型困惑）
    
    TODO: [RAG] 历史对话注入优化
        1. 接收的 history 应为 RAG 检索后的结果
        2. 检索结果按相关度排序，而非时间顺序
        3. 可考虑混合策略：最近 N 条 + 语义相关 M 条
        4. 对于 SQL 生成场景，优先召回包含相似表/字段的历史
    """
    if not history:
        return ""
    
    history_lines = []
    seen_questions = set()  # 用于去重
    
    for msg in history:
        content = msg.content.strip()
        
        # 跳过取消操作相关的消息
        if "已取消" in content or "已为您取消" in content:
            continue
        
        # 只保留用户消息，AI 的 SQL 回复不拼接（避免干扰模型判断）
        if msg.message_type == "user":
            # 清理内容，移除换行
            clean_content = content.replace("\n", " ")
            
            # 去重：相同的问题只保留第一次出现
            content_key = clean_content.lower().strip()
            if content_key in seen_questions:
                continue
            seen_questions.add(content_key)
            
            history_lines.append(f"User: {clean_content}")
    
    if not history_lines:
        return ""
    
    history_content = "\n".join(history_lines)
    
    return f"""
[Conversation History]
Previous user questions for context:
{history_content}"""


def build_context_block(
    schema_text: str,
    knowledge: list,
    history: list,
    db_type: str = None
) -> str:
    """
    组装完整的上下文块。
    
    Args:
        schema_text: 数据库 DDL（或 RAG 检索后的部分 DDL）
        knowledge: 领域知识列表（RAG 检索结果）
        history: 历史对话列表（RAG 检索结果）
        db_type: 数据库类型（mysql/postgresql/sqlite）
        
    Returns:
        str: 完整的上下文块
    
    TODO: [RAG] 上下文组装优化
        1. 动态计算各部分 Token 预算，避免超限
        2. 优先级：DDL > Knowledge > History
        3. 支持 Token 截断策略（truncate from tail）
        4. 添加上下文来源标注，便于调试
    """
    knowledge_section = build_knowledge_section(knowledge)
    history_section = build_history_section(history)
    
    # 数据库类型信息
    db_type_section = ""
    if db_type:
        db_type_upper = db_type.upper()
        db_type_section = f"\n[Database Type]\nTarget database: {db_type_upper}. Generate SQL compatible with {db_type_upper} syntax.\n"
    
    # TODO: [RAG] 后续添加 Token 计数和动态截断逻辑
    return f"""[Database DDL]
{schema_text}
{db_type_section}{knowledge_section}
{history_section}"""


def build_ai_messages(
    model_type: str,
    schema_text: str,
    question: str,
    history: list = None,
    knowledge: list = None,
    db_type: str = None
) -> list:
    """
    构建发送给 AI 的消息列表。
    
    Args:
        model_type: 模型类型 ('local_finetune' 或 'general_llm')
        schema_text: 数据库 DDL
        question: 用户当前问题
        history: 历史对话记录
        knowledge: 领域知识列表
        db_type: 数据库类型（mysql/postgresql/sqlite）
        
    Returns:
        list: 消息字典列表
    """
    history = history or []
    knowledge = knowledge or []
    
    context_block = build_context_block(schema_text, knowledge, history, db_type)
    
    if model_type == "local_finetune":
        prompt_content = f"""{SQL_GENERATION_SYSTEM_INSTRUCTION}
{context_block}

### User Question
{question}

### SQL Query
"""
        return [
            {"role": "system", "content": LOCAL_FINETUNE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_content}
        ]
    else:
        full_system_prompt = f"{SQL_GENERATION_SYSTEM_INSTRUCTION}\n{context_block}"
        return [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": question}
        ]


# =========================================================
# Mermaid ER 图生成相关配置
# =========================================================

MERMAID_ER_GENERATION_PROMPT = """You are a professional database designer.

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

MERMAID_THEME_CONFIG = {
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


def build_mermaid_init_directive() -> str:
    """
    构建 Mermaid 初始化指令（包含主题配置）。
    
    Returns:
        str: Mermaid init 指令字符串
    """
    import json
    return f"%%{{init: {json.dumps(MERMAID_THEME_CONFIG)} }}%%\n"
