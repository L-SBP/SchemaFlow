# backend/app/api/v1/api.py

from fastapi import APIRouter

# 引入所有 endpoints
from .endpoints import (
    auth, 
    project, 
    reports,  
    user, 
    admin,
    knowledge,
    chat,
    session,
    announcement # <--- 1. 导入新模块
)

api_router = APIRouter()

# ----------------------------------------------------
# 路由注册区
# ----------------------------------------------------

api_router.include_router(auth.router, prefix="/auth", tags=["I. 认证与授权"])
api_router.include_router(project.router, prefix="/projects", tags=["II. 项目管理"])
api_router.include_router(reports.router, tags=["III. 报表与查询"])
api_router.include_router(knowledge.router, tags=["IV. 业务术语表"])
api_router.include_router(user.router, prefix="/user", tags=["V. 用户设置"])
api_router.include_router(admin.router, tags=["VI. 管理员功能"])
api_router.include_router(chat.router, tags=["VII. 对话与消息管理"])
api_router.include_router(session.router, prefix="/sessions", tags=["VIII. 会话管理"])

# 2. 注册公告模块
# 这里的 prefix="/announcements" 完美对应了你文档中的 GET /announcements
api_router.include_router(announcement.router, prefix="/announcements", tags=["IX. 系统公告"])