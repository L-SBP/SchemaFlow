# backend/app/main.py

# 文件路径: app/main.py
import uvicorn
from core.config import config

# 5. 启动入口
if __name__ == "__main__":
    uvicorn.run(
        config.app.uvicorn, 
        host=config.app.host, 
        port=config.app.port, 
        reload=config.app.reload,
        proxy_headers=True,  # 信任代理头，正确解析 X-Forwarded-For 等
        forwarded_allow_ips="*"  # 允许所有来源的转发头（生产环境建议限制为代理服务器 IP）
    )