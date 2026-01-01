from openai import OpenAI
import os
import subprocess
import re
from datetime import datetime
import json
# 获取当前脚本所在的绝对路径（Windows Docker 挂载必须用绝对路径）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def extract_code_block(text):
    # extract mermaid codeblock
    pattern = r"```(?:\w*)\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def generate_er(requirement_text):
    mapping = {'gpt4': 'gpt-4o-2024-08-06',
                'chatgpt': 'gpt-3.5-turbo',
                'qwen': 'Qwen/Qwen3-32B',
                'deepseek': 'deepseek-v3-241226'}

    # 检查 API Key 是否存在
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("错误: 未找到环境变量 OPENAI_API_KEY")
        print("请在 PowerShell 中执行: $env:OPENAI_API_KEY='sk-你的key'")
        return None

    client = OpenAI(
        api_key=api_key,  
        base_url="https://ai.nengyongai.cn/v1"
    )
    
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

    
    print("正在调用大模型生成代码...")
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt + "\n\nRequirement:\n" + requirement_text,
                }
            ],
            model=mapping['gpt4'],    
        )
    except Exception as e:
        print(f"调用大模型失败: {e}")
        return None

    mermaid_code = extract_code_block(chat_completion.choices[0].message.content)
    if mermaid_code is None:
        mermaid_code = chat_completion.choices[0].message.content
    

    # ==========================================
    # 【修改点 1】: 构建嵌入式样式配置
    # ==========================================
    # 我们直接把配置写成 Mermaid 的 %%{init: ...}%% 头部
    theme_config = {
    "theme": "base",
    "themeVariables": {
        "primaryColor": "#ffffff",           # 表头背景（白色）
        "primaryTextColor": "#000000",       # 表头文字黑
        "primaryBorderColor": "#3370ff",     # 表框边框
        "lineColor": "#3370ff",              # 连线
        "tertiaryColor": "#e6f7ff",          # 字段行背景（淡蓝）
        "tertiaryBorderColor": "#3370ff",    # 字段行边框
        "tertiaryTextColor": "#000000",      # 字段文字黑
        "mainBkg": "#ffffff",                # 整体背景
        "edgeLabelBackground": "#fff"
    }
}
    # 将字典转为 json 字符串，并拼接到 mermaid 代码的最前面
    init_directive = f"%%{{init: {json.dumps(theme_config)} }}%%\n"
    final_content = init_directive + mermaid_code

    # ==========================================


    # 使用绝对路径处理目录
    directory = os.path.join(BASE_DIR, 'er_data')
    if not os.path.exists(directory):
        os.makedirs(directory)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{timestamp}.mmd"
    save_file_path = os.path.join(directory, file_name)

    with open(save_file_path, "w", encoding="utf-8") as f:
        f.write(final_content)

    print(f"Mermaid code已保存为 {save_file_path}")



    # 构造 Windows 兼容的 Docker 命令
    # 注意：Windows 路径包含反斜杠，Docker 挂载需要宿主机绝对路径
    cmd = [
        "docker", "run", "--rm",   # --rm: 运行完自动删除容器
        "-v", f"{directory}:/data", # 挂载绝对路径
        "minlag/mermaid-cli",           # 使用的镜像
        "-i", f"/data/{file_name}",     # 容器内读取路径
        "-o", f"/data/{file_name}.svg"  # 容器内输出路径
    ]

    print(f"正在执行 Docker 命令...")
    try:
        # 执行命令
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("命令执行成功")
        # print(result.stdout) 
        return os.path.join(directory, file_name + '.svg')
    except subprocess.CalledProcessError as e:
        print("命令执行失败，错误信息:")
        print(e.stderr)
        return None

# 测试入口
if __name__ == "__main__":
    requirement_text = """
    CREATE TABLE Student (
    StudentID VARCHAR(50) PRIMARY KEY,
    Name VARCHAR(100),
    Age INT
);

CREATE TABLE Course (
    CourseNumber INT PRIMARY KEY,
    CourseName VARCHAR(100),
    Credits INT,
    Lecturer VARCHAR(100),
    ClassTime DATETIME
);

CREATE TABLE Enrollment (
    StudentID VARCHAR(50),
    CourseNumber INT,
    EnrollmentDate DATETIME,
    PRIMARY KEY(StudentID, CourseNumber),
    FOREIGN KEY(StudentID) REFERENCES Student(StudentID),
    FOREIGN KEY(CourseNumber) REFERENCES Course(CourseNumber)
);

CREATE TABLE CoursePopularityPrediction (
    CourseNumber INT PRIMARY KEY,
    FOREIGN KEY(CourseNumber) REFERENCES Course(CourseNumber)
);"""
    
    svg_path = generate_er(requirement_text)
    if svg_path:
        print(f"SVG 生成路径: {svg_path}")