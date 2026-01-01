import json
import os
import random

# ================= 文件路径配置 =================
# 请确保这些文件都在你指定的目录下
SPIDER_TABLES_FILE = "./tables.json"
SPIDER_TRAIN_FILE = "./train_spider.json"
SPIDER_OTHERS_FILE = "./train_others.json" # [新增] README 提到的这部分数据
GENERATED_DML_FILE = "./spider_dml_extended.json" # 之前生成的增删改数据
OUTPUT_FILE = "./final_finetune_dataset.json"
# ===============================================

def parse_schema_map(tables_path):
    """预处理 tables.json，生成 db_id -> schema_text 的映射"""
    print(f"Loading schemas from {tables_path}...")
    with open(tables_path, 'r', encoding='utf-8') as f:
        tables_data = json.load(f)
    
    schema_map = {}
    for db in tables_data:
        db_id = db['db_id']
        table_names = db['table_names_original']
        column_names = db['column_names_original']
        column_types = db['column_types']
        primary_keys = db['primary_keys']
        
        tables_info = {}
        for idx, name in enumerate(table_names):
            tables_info[idx] = {"name": name, "columns": []}
            
        for col_idx, (table_idx, col_name) in enumerate(column_names):
            if table_idx == -1: continue
            col_type = column_types[col_idx]
            extra = " PK" if col_idx in primary_keys else ""
            tables_info[table_idx]["columns"].append(f"{col_name} ({col_type}){extra}")
            
        lines = []
        for t_info in tables_info.values():
            col_str = ", ".join(t_info["columns"])
            lines.append(f"Table {t_info['name']}: [{col_str}]")
        schema_map[db_id] = "\n".join(lines)
    return schema_map

def process_spider_file(filepath, schema_map, source_tag):
    """处理单个 Spider 格式的 json 文件"""
    processed = []
    if not os.path.exists(filepath):
        print(f"Warning: File {filepath} not found, skipping.")
        return processed
        
    print(f"Processing {source_tag} from {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for item in data:
        db_id = item['db_id']
        question = item['question']
        sql = item['query']
        schema_text = schema_map.get(db_id, "")
        
        processed.append({
            "instruction": question,
            "input": f"Schema:\n{schema_text}",
            "output": sql,
            "source": source_tag,
            "db_id": db_id
        })
    return processed

def main():
    if not os.path.exists(SPIDER_TABLES_FILE):
        print(f"Error: {SPIDER_TABLES_FILE} not found.")
        return
    schema_map = parse_schema_map(SPIDER_TABLES_FILE)
    
    final_dataset = []
    
    # 1. 处理 train_spider.json
    final_dataset.extend(process_spider_file(SPIDER_TRAIN_FILE, schema_map, "spider_main"))
    
    # 2. [新增] 处理 train_others.json (根据 README 要求)
    final_dataset.extend(process_spider_file(SPIDER_OTHERS_FILE, schema_map, "spider_others"))

    # 3. 合并生成的 DML 数据 (Insert/Update/Delete)
    if os.path.exists(GENERATED_DML_FILE):
        print(f"Merging generated DML data from {GENERATED_DML_FILE}...")
        with open(GENERATED_DML_FILE, 'r', encoding='utf-8') as f:
            dml_data = json.load(f)
        for item in dml_data:
            item["source"] = "generated_dml"
            final_dataset.append(item)
    else:
        print("Warning: Generated DML file not found.")

    # 4. 打乱并保存
    print(f"Shuffling {len(final_dataset)} total examples...")
    random.shuffle(final_dataset)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully saved merged dataset to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()