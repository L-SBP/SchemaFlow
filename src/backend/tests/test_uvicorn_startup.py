import uvicorn
import os
import sys
from app.server import my_app
from app.core.config import config

print(f"Process ID: {os.getpid()}")
print(f"UVicorn configuration:")
print(f"- Host: {config.app.host}")
print(f"- Port: {config.app.port}")
print(f"- Reload: {config.app.reload}")
print(f"- App: {config.app.uvicorn}")

# 直接启动应用而不使用uvicorn.run()
if __name__ == "__main__":
    # 使用uvicorn命令行参数启动
    sys.argv = [
        "uvicorn",
        config.app.uvicorn,
        "--host", config.app.host,
        "--port", str(config.app.port),
        "--reload"
    ]
    uvicorn.main()
