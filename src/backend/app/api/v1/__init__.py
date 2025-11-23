from fastapi import APIRouter
from .endpoints import chat, sessions

api_router = APIRouter()

# 注册聊天相关路由
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])