from fastapi import APIRouter

api_router = APIRouter()

from api.v1.endpoints import (
    auth, users, projects, query,
    knowledge, announcements, admin_analytics, admin_users
)
# from api.v1.endpoints import reports


# api_router.include_router(reports.router, tags=["Reports"])

api_router.include_router(auth.auth_router, prefix="/auth", tags=["I. 认证与授权"])
# api_router.include_router(users.router, prefix="/users/me", tags=["II. 用户设置"])
# api_router.include_router(projects.router, prefix="/projects", tags=["III. 项目管理"])
#
# # IV. 智能查询核心 (路由较多)
# api_router.include_router(query.router_sessions, tags=["IV. 智能查询核心 (Session)"])
# api_router.include_router(query.router_statements, tags=["IV. 智能查询核心 (Statement)"])
# api_router.include_router(query.router_messages, tags=["IV. 智能查询核心 (Message)"])
# api_router.include_router(query.router_results, tags=["IV. 智能查询核心 (Result)"])
#
# api_router.include_router(knowledge.router, tags=["VI. 知识库"])
# api_router.include_router(announcements.router, tags=["VII. 公告管理"])
#
# # VIII. 后台管理 (Admin)
# api_router.include_router(admin_analytics.router, prefix="/admin/analytics", tags=["V. 报表与分析 (Admin)"])
# api_router.include_router(admin_users.router, prefix="/admin/users", tags=["VIII. 后台管理 (Admin Users)"])