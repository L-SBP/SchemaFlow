import requests
import json
import random
import string
import os

# 导入上面的纯提取函数
from src.backend.tests.ai.test_html2schema import get_schema_design, get_ddl_statements

def generate_schema(requirements_text):
    base_host = "http://43.154.73.48:5000"
    session_hash = ''.join(random.choices(string.ascii_lowercase + string.digits, k=11))
    
    # 注意：inputs 的顺序绝对不能动
    inputs = [
        "gpt4",              # 1. Model
        "test_db",           # 2. DB Name
        requirements_text,   # 3. Requirements
        "MySQL"              # 4. DBMS
    ]

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # 1. 提交任务
    try:
        resp = requests.post(f"{base_host}/gradio_api/queue/join", 
                           json={"data": inputs, "session_hash": session_hash, "fn_index": 0}, 
                           headers=headers, timeout=10)
        if resp.status_code != 200: return {"status": "error", "message": resp.text}
    except Exception as e: return {"status": "error", "message": str(e)}

    # 2. 获取结果
    print("等待处理...", end="", flush=True)
    try:
        resp = requests.get(f"{base_host}/gradio_api/queue/data?session_hash={session_hash}", 
                          headers=headers, stream=True, timeout=120)
        
        for line in resp.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data: '):
                    print(".", end="", flush=True)
                    try:
                        msg = json.loads(decoded[6:])
                        if msg.get('msg') == 'process_completed':
                            output_data = msg.get('output', {}).get('data', [])
                            if output_data:
                                html_content = output_data[0]
                                
                                # 保存日志以便排查
                                with open("res.html", "w", encoding="utf-8") as f:
                                    f.write(html_content)
                                
                                # === 关键点：只提取，不解析 ===
                                # 这里拿到的是一大段纯文本字符串
                                raw_schema = get_schema_design(html_content)
                                raw_ddl = get_ddl_statements(html_content)
                                
                                print("\n✅ 获取成功")
                                return {
                                    "status": "success",
                                    "schema": raw_schema, # 原始文本块
                                    "ddl": raw_ddl        # 原始SQL块
                                }
                    except: continue
    except Exception as e: return {"status": "error", "message": str(e)}
    
    return {"status": "error", "message": "超时"}

if __name__ == "__main__":
    req = "A university needs a student course selection management system to maintain and track students' course selection information. Students have\ninformation such as student ID, name, age, the name of the course chosen by the student, etc. Each student can take multiple courses and can drop or\nchange courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The\npopularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support\nfor academic decision-making"
    res = generate_schema(req)
    if res['status'] == 'success':
        print("\n[Schema Raw Data]\n", res['schema'])
        print("\n[DDL Raw Data]\n", res['ddl'])