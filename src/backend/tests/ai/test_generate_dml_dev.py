import json
import os
import httpx
import asyncio
from tqdm import tqdm

# ================= 配置区域 =================
# 必须确保这些文件存在 (保持原有的相对路径)
SPIDER_TABLES_PATH = "../tables.json"
SPIDER_DEV_PATH = "../dev.json"  # 指向 Spider 的 dev.json
# SPIDER_OTHERS_PATH = "../train_others.json"

# 输出文件
OUTPUT_FILE = "./spider_dml_dev.json" # 输出到新的 dev 文件

# AI 服务配置
#  /v1/chat/completions
AI_SERVICE_URL = "https://ai.nengyongai.cn/v1/chat/completions"
AI_API_KEY = "sk-VwmLWgJlhLpNCyrP5IcTfvsBZp9VfhQqXfqcz7LH35xn5lhn"
AI_MODEL = "qwen-turbo"


# 并发数
CONCURRENCY_LIMIT = 1
# ===========================================

SYSTEM_PROMPT = """You are a SQL dataset generator. 
Your task is to generate pairs of "Natural Language Instruction" and "SQL Command" based on the provided database schema.

### STRICT RULES FOR SQL GENERATION:

1. **Focus ONLY on DML**: Generate INSERT, UPDATE, and DELETE statements. NO SELECT.

2. **Handling Primary Keys (PK) - CRITICAL**: 
   - **CASE 1: Numeric PK** (e.g., id int): TREAT AS AUTO-INCREMENT. **DO NOT** insert value.
     - Correct: INSERT INTO Student (Name) VALUES ('John');
   - **CASE 2: Text/String PK** (e.g., id varchar, code text): **YOU MUST GENERATE A VALUE**.
     - Correct: INSERT INTO Course (Course_Code, Name) VALUES ('CS101', 'Intro to CS');
     - Wrong: INSERT INTO Course (Name) VALUES ('Intro to CS');
   - **CASE 3: Composite/Foreign Keys**: Always insert values for foreign keys and junction tables.

3. **Real-world Business Logic (User Intent)**:
   - Users rarely know IDs (e.g., "Delete ID 5"). They use names, titles, or codes.
   - **Instruction**: Use natural language references.
     - Good: "Delete the student named John Doe."
     - Good: "Update the price of the 'Basic Plan'."
     - Avoid: "Delete student with ID 5." (Unless testing specific ID logic)
   - **WHERE Clause**: Match the Instruction.
     - If instruction says "John Doe", SQL must use `WHERE Name = 'John Doe'`.
     - Do NOT look up the ID internally to use in the SQL unless the user explicitly provided the ID.

4. **Diversity**: Mix simple conditions and specific business logic.
"""

USER_TEMPLATE = """
Here is the schema for the database "{db_id}":
{schema_text}

Please generate {count} diverse pairs of (Instruction, SQL) covering INSERT, UPDATE, and DELETE operations.
Make sure the SQL is valid based on the schema provided.
The "Instruction" should sound like a real user request.

Return the result strictly in valid JSON format like this list:
[
  {{"instruction": "Delete the student with ID 1", "output": "DELETE FROM student WHERE id = 1;"}},
  {{"instruction": "Change the name of course CS101 to 'Intro to AI'", "output": "UPDATE course SET name = 'Intro to AI' WHERE course_code = 'CS101';"}}
]
"""

def get_dev_db_ids():
    """获取所有 Dev 集涉及的数据库 ID"""
    db_ids = set()
    
    # 修改这里读取 SPIDER_DEV_PATH
    if os.path.exists(SPIDER_DEV_PATH):
        with open(SPIDER_DEV_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                db_ids.add(item['db_id'])
                
    print(f"Found {len(db_ids)} unique databases in DEV set.")
    return db_ids

def parse_spider_schema(table_entry):
    """将 Spider 的 tables.json 条目转换为文本 Schema"""
    db_id = table_entry['db_id']
    table_names = table_entry['table_names_original']
    column_names = table_entry['column_names_original']
    column_types = table_entry['column_types']
    primary_keys = table_entry['primary_keys']
    foreign_keys = table_entry['foreign_keys']

    tables = {} 
    for idx, name in enumerate(table_names):
        tables[idx] = {"name": name, "columns": []}

    for col_idx, (table_idx, col_name) in enumerate(column_names):
        if table_idx == -1: continue
        col_type = column_types[col_idx]
        is_pk = col_idx in primary_keys
        
        col_desc = f"{col_name} ({col_type})"
        if is_pk: col_desc += " PK"
        tables[table_idx]["columns"].append(col_desc)

    schema_lines = []
    for t_info in tables.values():
        cols_str = ", ".join(t_info["columns"])
        schema_lines.append(f"Table {t_info['name']}: [{cols_str}]")
    
    if foreign_keys:
        fk_lines = []
        for src, tgt in foreign_keys:
            try:
                src_table = column_names[src][0]
                src_col = column_names[src][1]
                tgt_table = column_names[tgt][0]
                tgt_col = column_names[tgt][1]
                fk_lines.append(f"FK: {table_names[src_table]}.{src_col} -> {table_names[tgt_table]}.{tgt_col}")
            except: pass
        if fk_lines:
            schema_lines.append("Relationships: " + "; ".join(fk_lines))

    return "\n".join(schema_lines)

async def generate_for_db(client, db_entry, semaphore):
    async with semaphore:
        db_id = db_entry['db_id']
        schema_text = parse_spider_schema(db_entry)
        
        prompt = USER_TEMPLATE.format(db_id=db_id, schema_text=schema_text, count=30)
        
        payload = {
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 8192
        }

        try:
            # 超时时间设长一点，防止生成中断
            response = await client.post(AI_SERVICE_URL, json=payload, headers={"Authorization": f"Bearer {AI_API_KEY}"}, timeout=90)
            
            # 检查 HTTP 状态码
            if response.status_code != 200:
                print(f"Error generating for {db_id}: HTTP {response.status_code} - {response.text[:100]}")
                return []

            # 解析响应
            try:
                resp_json = response.json()
                content = resp_json['choices'][0]['message']['content']
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                # 【新增】详细错误打印，帮助定位问题
                print(f"Error parsing API response for {db_id}: {e}")
                print(f"Raw Response: {response.text[:200]}...") # 打印前200个字符看看是什么
                return []
            
            # 1. 清洗 Markdown 标记 (保持原有的逻辑)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            # 2. 去除首尾空白
            content = content.strip()

            # === 【新增】修复非法转义字符 ===
            # 将 JSON 中非法的 \' 替换为合法的 '
            # 注意：使用 r"\'" 表示原始字符串
            content = content.replace(r"\'", "'") 
            # ==============================

            # 3. 解析 JSON
            try:
                # strict=False 允许字符串中包含控制字符 (解决 Invalid control character)
                data_pairs = json.loads(content, strict=False)
            except json.JSONDecodeError as e:
                # 如果还是报错，尝试一种更暴力的清洗方式（仅作为后备方案）
                print(f"Standard parse failed for {db_id}, trying fallback cleanup...")
                try:
                    # 仅在非结构位置替换（极简处理：假设非法字符只出现在字符串值里）
                    # 注意：这仍然有风险，但在数据生成脚本中通常够用
                    import re
                    # 移除所有非 JSON 结构的换行符（这很难完美做到，不如直接跳过）
                    # 建议：如果 strict=False 还是挂了，打印内容人工检查，或者直接让模型重试
                    print(f"FAILED CONTENT PREVIEW: {content[:100]}...")
                    print(f"Raw Content: {content}")
                    return [] 
                except:
                    return []
            
            formatted_data = []
            for item in data_pairs:
                formatted_data.append({
                    "instruction": item['instruction'],
                    "input": f"Schema:\n{schema_text}",
                    "output": item['output'],
                    "db_id": db_id,
                    "type": "DML_generated"
                })
            
            return formatted_data

        except Exception as e:
            # 打印错误但不中断整个过程
            print(f"Error generating for {db_id}: {e}")
            return []

async def main():
    if not os.path.exists(SPIDER_TABLES_PATH):
        print(f"Error: {SPIDER_TABLES_PATH} not found.")
        return

    # 1. 获取训练集白名单
    dev_db_ids = get_dev_db_ids() # 修改为调用上面的新函数
    if not dev_db_ids:
        print("Error: No training databases found. Check your train_spider/others paths.")
        return

    # 2. 读取所有 Tables
    print("Loading Spider tables...")
    with open(SPIDER_TABLES_PATH, 'r', encoding='utf-8') as f:
        all_tables = json.load(f)

    # 3. 过滤
    # 这一步会把 all_tables 中不属于 dev 集的数据库过滤掉
    target_dbs = [db for db in all_tables if db['db_id'] in dev_db_ids]
    
    # 4. 并发生成
    results = []
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    async with httpx.AsyncClient() as client:
        tasks = [generate_for_db(client, db, semaphore) for db in target_dbs]
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            batch = await f
            results.extend(batch)

    print(f"Generation complete. Total items: {len(results)}")
    
    # 5. 保存
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())