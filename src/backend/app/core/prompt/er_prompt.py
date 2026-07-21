from langchain_core.prompts import ChatPromptTemplate

ER_SYSTEM_PROMPT = """你是一位数据库可视化专家。根据给定的 Schema 定义，生成 Mermaid ER 图代码。

要求：
1. 使用 erDiagram 语法
2. 每个实体列出关键字段
3. 标注实体间关系（一对一、一对多、多对多）
4. 只输出有效的 Mermaid 代码，不要任何解释文字
"""

ER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", ER_SYSTEM_PROMPT),
    ("user", "请为以下 Schema 生成 Mermaid ER 图：\n\n{schema_text}"),
])