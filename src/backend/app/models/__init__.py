# backend/app/models/__init__.py

# 导入所有模型，确保 SQLAlchemy 能找到它们
from .user_account import UserAccount
from .user_login_history import UserLoginHistory
from .project import Project
from .database_instance import DatabaseInstance
from .session import Session
from .message import Message  # <--- 必须导入这个，解决你的报错
from .ai_generated_statement import AIGeneratedStatement
from .query_result import QueryResult
from .operation_log import OperationLog
from .violation_log import ViolationLog
from .user_ban_log import UserBanLog
from .unban_request import UnbanRequest
from .system_announcement import SystemAnnouncement
from .user_profile_change_log import UserProfileChangeLog
from .domain_knowledge import DomainKnowledge