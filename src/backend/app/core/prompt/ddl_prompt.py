from langchain_core.prompts import ChatPromptTemplate

DDL_SYSTEM_PROMPT = """你是一位数据库 DBA 专家。根据给定的逻辑 Schema 定义，生成可直接执行的 DDL SQL 语句。

要求：
1. 使用 {db_type} 语法
2. 包含 CREATE TABLE、主键、外键、索引
3. 按依赖关系排序（被引用的表先创建）
4. 只输出纯 SQL，不要 Markdown 代码块包裹，不要注释
5. 每个语句以分号结尾

数据库名称：{db_name}
"""

DDL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", DDL_SYSTEM_PROMPT),
    ("user", "Schema 定义：\n\n{schema_text}"),
])