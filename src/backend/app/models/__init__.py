"""
数据模型包初始化。

导出所有 ORM 模型，并定义了它们的导入顺序以解决依赖关系。
"""

# backend/app/models/__init__.py

# 导入所有模型，确保 SQLAlchemy 能找到它们
# 注意：导入顺序非常重要，应遵循依赖关系，先导入被依赖的表（基础表），后导入依赖表

# 1. 无外键依赖的基础表（必须最先）
from .user_account import UserAccount
from .user_login_history import UserLoginHistory
from .project import Project
from .database_instance import DatabaseInstance

# 2. Session（很多表依赖它，如 Message, OperationLog）
from .session import Session

# 3. 依赖 Session 的表
from .operation_log import OperationLog
from .message import Message  # Message 依赖 Session

# 4. 依赖 Message 的表
from .ai_generated_statement import AIGeneratedStatement
from .query_result import QueryResult

# 5. 其他无环依赖的表
from .violation_log import ViolationLog
from .user_ban_log import UserBanLog
from .unban_request import UnbanRequest
from .system_announcement import SystemAnnouncement
from .user_profile_change_log import UserProfileChangeLog
from .domain_knowledge import DomainKnowledge