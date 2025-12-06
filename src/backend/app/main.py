# 文件路径: app/main.py (覆盖全部内容)
import uvicorn
from core.config import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
# 修正导入：使用最上层 app 包下的 api_router
#from app.api.v1.api import api_router
# from api.v1.api import api_router
# ... (FastAPI 实例创建和路由挂载逻辑，与之前给出的代码相同) ...
# 为了简化，只显示关键部分

#app = FastAPI(title="智能数据库助手 API")
# ... CORS 配置 ...
#app.include_router(api_router, prefix="/api/v1")

# 5. 启动入口
if __name__ == "__main__":
    uvicorn.run(config.app.uvicorn, host=config.app.host, port=config.app.port, reload=config.app.reload)