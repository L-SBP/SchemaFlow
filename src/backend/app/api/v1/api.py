from fastapi import APIRouter

# 确保所有 endpoints 文件都被正确导入（相对导入是关键）
from .endpoints import auth, project, reports, glossary, user

api_router = APIRouter()

# ----------------------------------------------------
# 路由注册区：必须包含所有模块的 include_router 语句
# ----------------------------------------------------

# 1. 认证模块 (已存在)
api_router.include_router(auth.router, prefix="/auth", tags=["I. 认证与授权"])

# 2. 项目管理模块 (新增)
api_router.include_router(project.router, prefix="/projects", tags=["II. 项目管理"])

# 3. 报表查询模块 (新增)
# 注意：reports.py 文件中的路由路径包含了 /reports 和 /history-queries，
# 所以这里注册时无需再添加 prefix，直接挂载即可。
api_router.include_router(reports.router, tags=["III. 报表与查询"])

# 4. 业务术语表模块 (新增)
api_router.include_router(glossary.router, prefix="/glossary", tags=["IV. 业务术语表"])

# 5. 用户设置模块 (新增)
api_router.include_router(user.router, prefix="/user", tags=["V. 用户设置"])# api_router.include_router(admin_users.router, prefix="/admin/users", tags=["VIII. 后台管理 (Admin Users)"])