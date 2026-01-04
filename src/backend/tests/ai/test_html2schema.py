from bs4 import BeautifulSoup

def get_schema_design(html_content):
    """
    (保持不变) 提取 Logical Design 下的所有纯文本
    """
    if not html_content:
        return ""
        
    soup = BeautifulSoup(html_content, 'html.parser')
    extracted_text = []
    
    start_node = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3', 'h4'] and 'Logical Design' in tag.get_text())
    
    if not start_node:
        return ""

    current = start_node.find_next_sibling()
    while current:
        if current.name in ['h1', 'h2', 'h3', 'h4']:
            break
        text = current.get_text(separator='\n', strip=True)
        if text:
            extracted_text.append(text)
        current = current.find_next_sibling()
        
    return "\n\n".join(extracted_text)

def get_ddl_statements(html_content):
    """
    提取所有 SQL 代码块，并将 CREATE DATABASE 语句移动到最前方
    """
    if not html_content:
        return ""
        
    soup = BeautifulSoup(html_content, 'html.parser')
    ddl_list = []
    
    # 1. 先按页面顺序提取所有 SQL 块
    sql_blocks = soup.find_all('code', class_='language-sql')
    
    for block in sql_blocks:
        sql_text = block.get_text().strip()
        if sql_text:
            ddl_list.append(sql_text)

    # 2. 重新排序：寻找包含 'CREATE DATABASE' 的块
    create_db_index = -1
    for i, sql in enumerate(ddl_list):
        # 不区分大小写查找
        if "CREATE DATABASE" in sql.upper():
            create_db_index = i
            break
    
    # 3. 如果找到了，且它不在第一位，就把它移到最前面
    if create_db_index > 0:
        create_db_sql = ddl_list.pop(create_db_index) # 拔出来
        ddl_list.insert(0, create_db_sql)             # 插到头
        
    return "\n\n".join(ddl_list)

# ================= 测试代码 =================
if __name__ == "__main__":
    import os
    if os.path.exists("res.html"):
        with open("res.html", "r", encoding="utf-8") as f:
            content = f.read()
            print("--- DDL (已自动重排序) ---")
            print(get_ddl_statements(content))