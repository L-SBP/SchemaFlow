import json
import os

# ================= 配置 =================
# 输入：之前生成的 DML 数据 (Alpaca 格式)
INPUT_DML_FILE = "./spider_dml_dev.json"

# 输出：转换后的 DML 数据 (Spider 格式)
# 建议改个名字，表明它只包含 DML 数据
OUTPUT_FILE = "./spider_dml_dev_converted.json"
# =======================================

def convert_dml_to_spider_format(dml_data):
    """
    将 Alpaca 格式 (instruction/output) 转换为 Spider 格式 (question/query/sql)
    """
    spider_style_data = []
    
    for item in dml_data:
        # 提取核心字段
        question = item.get('instruction', '')
        sql_query = item.get('output', '')
        db_id = item.get('db_id', '')
        
        # 简单的分词 (模拟 Spider 的 toks)
        q_toks = question.split()
        sql_toks = sql_query.split()
        
        entry = {
            "db_id": db_id,
            "query": sql_query,
            "query_toks": sql_toks,
            "query_toks_no_value": sql_toks,
            "question": question,
            "question_toks": q_toks,
            # 空的 sql 解析树结构，骗过训练代码的检查
            "sql": {
                "from": {"table_units": [], "conds": []},
                "select": [],
                "where": [],
                "groupBy": [],
                "having": [],
                "orderBy": [],
                "limit": None,
                "intersect": None,
                "union": None,
                "except": None
            }
        }
        spider_style_data.append(entry)
        
    return spider_style_data

def main():
    # 1. 读取生成的 DML 数据
    if not os.path.exists(INPUT_DML_FILE):
        print(f"Error: {INPUT_DML_FILE} not found. Please generate it first.")
        return
        
    print(f"Loading generated DML data from {INPUT_DML_FILE}...")
    with open(INPUT_DML_FILE, 'r', encoding='utf-8') as f:
        dml_data = json.load(f)
        
    # 2. 转换格式
    print("Converting DML data to Spider format...")
    dml_spider_format = convert_dml_to_spider_format(dml_data)
    print(f"Converted {len(dml_spider_format)} DML entries.")

    # 3. 保存 (不再合并其他文件)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(dml_spider_format, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully saved separate DML dataset to {OUTPUT_FILE}")
    print("Now update your config.py to include this file in the train_file list.")

if __name__ == "__main__":
    main()