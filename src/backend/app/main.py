# backend/app/main.py

# 文件路径: app/main.py
import uvicorn
from core.config import config

# 5. 启动入口
if __name__ == "__main__":
    uvicorn.run(config.app.uvicorn, host=config.app.host, port=config.app.port, reload=config.app.reload)