from gradio_client import Client

client = Client("http://43.154.73.48:5000/")

# 注意：去掉 model_name= 等前缀，直接按顺序传值
result = client.predict(
    "gpt4",                # 第1个位置参数 (model_name)
    "relation_mcp_test",   # 第2个位置参数 (database_name)
    "Hello!!",             # 第3个位置参数 (requirement_text)
    api_name="/run_agent_system" # 这个 api_name 参数必须保留名字
)

print(result)