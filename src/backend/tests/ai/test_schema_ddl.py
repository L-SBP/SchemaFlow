import os
from openai import OpenAI

# 配置你的 API Key 和 Base URL
# 如果使用 OpenAI 官方：不需要改 base_url
# 如果使用国内模型（如 DeepSeek），base_url 通常是 https://api.deepseek.com/v1
client = OpenAI(
    api_key="sk-YQjmNgkBJqRTsZCsr7r0zkHoLb6G0exL9u8gEkJTf5oZQXmE",  # 替换这里
    base_url="http://www.ai678.top:8081/v1"  # 根据服务商修改
)

def generate_database_schema(requirements: str, db_type: str = "MySQL") -> str:
    """
    根据用户需求和数据库类型生成 DDL。
    
    Args:
        requirements (str): 用户的功能需求描述。
        db_type (str): "MySQL" 或 "PostgreSQL"。
        
    Returns:
        str: 生成的 SQL DDL 语句。
    """
    
    # 1. 构建 System Prompt (角色设定)
    # 我们设定它为资深数据库架构师，强调规范性、范式和特定方言
    system_prompt = f"""
    You are a Senior Database Architect. 
    Your task is to design a database schema based on the user's requirements.
    
    Target Database Dialect: **{db_type}**
    
    Rules:
    1. Output strictly valid SQL DDL statements (CREATE TABLE, etc.).
    2. Use appropriate data types for {db_type} (e.g., use SERIAL/UUID for Postgres, AUTO_INCREMENT for MySQL).
    3. Include Primary Keys, Foreign Keys, and NOT NULL constraints where logical.
    4. Add comments to tables and columns (COMMENT ON for Postgres, COMMENT '...' for MySQL).
    5. Follow 3rd Normal Form (3NF) usually, unless performance suggests otherwise.
    6. Wrap the SQL code in a markdown block (```sql ... ```).
    7. After the code, provide a very brief explanation of the design logic.
    """

    # 2. 构建 User Prompt (具体任务)
    user_prompt = f"""
    Here are the requirements for the system:
    "{requirements}"
    
    Please generate the full DDL script.
    """

    try:
        # 3. 调用大模型
        response = client.chat.completions.create(
            model="claude-sonnet-4-5-20250929",  # 或者 gpt-3.5-turbo, deepseek-chat 等
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2, # 较低的温度可以让输出更稳定、严谨
        )
        
        return response.choices[0].message.content

    except Exception as e:
        return f"Error generating schema: {str(e)}"

# --- 主程序入口 ---
if __name__ == "__main__":
    print("--- 智能数据库 Schema 生成器 ---")
    
    # 获取输入
    req_input = input("请输入需求描述 (例如: 一个简单的电商系统，包含用户、商品和订单): \n")
    if not req_input:
        req_input = "一个包含用户、文章和评论的博客系统"
    
    # 选择数据库类型
    print("\n请选择数据库类型:")
    print("1. MySQL")
    print("2. PostgreSQL")
    choice = input("输入选项 (1/2): ")
    
    target_db = "MySQL" if choice != "2" else "PostgreSQL"
    
    print(f"\n正在为 [{target_db}] 生成 Schema，请稍候...\n")
    
    # 生成并打印
    result = generate_database_schema(req_input, target_db)
    
    print("-" * 30)
    print(result)
    print("-" * 30)