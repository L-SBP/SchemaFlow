"""
Redis 键前缀管理系统

该模块提供统一的 Redis 键生成和管理功能，确保所有 Redis 键遵循一致的命名规范。
支持环境隔离、键分类和统一的键生成接口。
"""

from typing import Optional, Any
from core.config import config


class RedisKeyManager:
    """
    Redis 键管理器类
    
    提供统一的键生成方法，支持环境隔离和键分类管理。
    """
    
    # 键前缀常量（按功能分类）
    # 认证相关
    TOKEN_PREFIX = "token"
    # 公告相关
    ANNOUNCEMENT_PREFIX = "announcement"
    # 密码重置相关
    PASSWORD_RESET_PREFIX = "pwdreset"
    # 验证码相关
    VERIFICATION_PREFIX = "verification"
    # 频率限制相关
    FREQUENCY_LIMIT_PREFIX = "freq"
    # 用户相关
    USER_PREFIX = "user"
    # 系统相关
    SYSTEM_PREFIX = "system"
    # 项目相关
    PROJECT_PREFIX = "project"
    # 数据库实例相关
    DATABASE_PREFIX = "db"
    # SQL执行相关
    SQL_PREFIX = "sql"
    # 缓存相关
    CACHE_PREFIX = "cache"
    # API响应相关
    API_PREFIX = "api"
    # 配置相关
    CONFIG_PREFIX = "config"
    
    @classmethod
    def _get_base_prefix(cls) -> str:
        """
        获取基础前缀（包含环境隔离前缀）
        
        Returns:
            str: 基础前缀
        """
        return config.redis.key_prefix
    
    @classmethod
    def generate_key(cls, *parts: str, prefix: Optional[str] = None) -> str:
        """
        生成统一格式的 Redis 键
        
        Args:
            *parts: 键的各个部分
            prefix: 可选的自定义前缀
            
        Returns:
            str: 完整的 Redis 键
        """
        # 构建键的所有部分
        key_parts = []
        
        # 添加基础前缀（用于环境隔离）
        base_prefix = cls._get_base_prefix()
        if base_prefix:
            key_parts.append(base_prefix)
        
        # 添加自定义前缀
        if prefix:
            key_parts.append(prefix)
        
        # 添加其他部分
        key_parts.extend(parts)
        
        # 使用冒号连接所有部分
        return ":".join(key_parts)
    
    # 认证相关键生成方法
    @classmethod
    def get_token_key(cls, token: str) -> str:
        """
        生成 Token 键
        
        Args:
            token: Token 值
            
        Returns:
            str: Token 键
        """
        return cls.generate_key(cls.TOKEN_PREFIX, token)
    
    # 公告相关键生成方法
    @classmethod
    def get_announcement_list_key(cls, page: int, page_size: int) -> str:
        """
        生成公告列表键
        
        Args:
            page: 页码
            page_size: 每页数量
            
        Returns:
            str: 公告列表键
        """
        return cls.generate_key(
            cls.ANNOUNCEMENT_PREFIX, 
            "list", 
            "published", 
            f"page_{page}", 
            f"size_{page_size}"
        )
    
    @classmethod
    def get_announcement_detail_key(cls, announcement_id: int) -> str:
        """
        生成公告详情键
        
        Args:
            announcement_id: 公告ID
            
        Returns:
            str: 公告详情键
        """
        return cls.generate_key(cls.ANNOUNCEMENT_PREFIX, "detail", str(announcement_id))
    
    @classmethod
    def get_announcement_list_pattern(cls) -> str:
        """
        生成公告列表键的匹配模式
        
        Returns:
            str: 公告列表键匹配模式
        """
        return cls.generate_key(cls.ANNOUNCEMENT_PREFIX, "list", "published", "*")
    
    @classmethod
    def get_announcement_detail_pattern(cls) -> str:
        """
        生成公告详情键的匹配模式
        
        Returns:
            str: 公告详情键匹配模式
        """
        return cls.generate_key(cls.ANNOUNCEMENT_PREFIX, "detail", "*")
    
    # 密码重置相关键生成方法
    @classmethod
    def get_password_reset_key(cls, email: str) -> str:
        """
        生成密码重置验证码键
        
        Args:
            email: 用户邮箱
            
        Returns:
            str: 密码重置验证码键
        """
        return cls.generate_key(cls.PASSWORD_RESET_PREFIX, "code", email)
    
    # 验证码相关键生成方法
    @classmethod
    def get_verification_key(cls, email: str) -> str:
        """
        生成验证码键
        
        Args:
            email: 用户邮箱
            
        Returns:
            str: 验证码键
        """
        return cls.generate_key(cls.VERIFICATION_PREFIX, email)
    
    # 频率限制相关键生成方法
    @classmethod
    def get_frequency_limit_key(cls, user_id: int, action: Optional[str] = None) -> str:
        """
        生成频率限制键
        
        Args:
            user_id: 用户ID
            action: 操作类型
            
        Returns:
            str: 频率限制键
        """
        if action:
            return cls.generate_key(cls.FREQUENCY_LIMIT_PREFIX, cls.USER_PREFIX, str(user_id), action)
        return cls.generate_key(cls.FREQUENCY_LIMIT_PREFIX, cls.USER_PREFIX, str(user_id))
    
    # 密码重置相关键生成方法
    @classmethod
    def get_password_reset_rate_limit_key(cls, email: str, client_ip: Optional[str] = None) -> str:
        """
        生成密码重置频率限制键
        
        Args:
            email: 用户邮箱
            client_ip: 客户端IP
            
        Returns:
            str: 频率限制键
        """
        if client_ip:
            return cls.generate_key(cls.PASSWORD_RESET_PREFIX, "rl", "ip", client_ip)
        return cls.generate_key(cls.PASSWORD_RESET_PREFIX, "rl", "email", email.lower().strip())
    
    @classmethod
    def get_password_reset_code_key(cls, email: str) -> str:
        """
        生成密码重置验证码键
        
        Args:
            email: 用户邮箱
            
        Returns:
            str: 密码重置验证码键
        """
        return cls.generate_key(cls.PASSWORD_RESET_PREFIX, "code", email.lower().strip())
    
    # 用户相关键生成方法
    @classmethod
    def get_user_info_key(cls, user_id: int) -> str:
        """
        生成用户信息键
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 用户信息键
        """
        return cls.generate_key(cls.USER_PREFIX, "info", str(user_id))
    
    @classmethod
    def get_user_projects_key(cls, user_id: int) -> str:
        """
        生成用户项目列表键
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 用户项目列表键
        """
        return cls.generate_key(cls.USER_PREFIX, "projects", str(user_id))
    
    @classmethod
    def get_user_databases_key(cls, user_id: int) -> str:
        """
        生成用户数据库列表键
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 用户数据库列表键
        """
        return cls.generate_key(cls.USER_PREFIX, "databases", str(user_id))
    
    @classmethod
    def get_project_list_key(cls, user_id: int, search: Optional[str] = None, 
                           page: int = 1, page_size: int = 10) -> str:
        """
        生成用户项目列表键（包含搜索条件和分页参数）
        
        Args:
            user_id: 用户ID
            search: 搜索条件
            page: 页码
            page_size: 页大小
            
        Returns:
            str: 用户项目列表键
        """
        # 处理搜索条件，None时使用空字符串
        search_str = search or ""
        return cls.generate_key(cls.USER_PREFIX, "projects", str(user_id), 
                              f"search:{search_str}", f"page:{page}", f"size:{page_size}")
    
    # 项目相关键生成方法
    @classmethod
    def get_project_info_key(cls, project_id: int) -> str:
        """
        生成项目信息键
        
        Args:
            project_id: 项目ID
            
        Returns:
            str: 项目信息键
        """
        return cls.generate_key(cls.PROJECT_PREFIX, "info", str(project_id))
    
    @classmethod
    def get_project_members_key(cls, project_id: int) -> str:
        """
        生成项目成员列表键
        
        Args:
            project_id: 项目ID
            
        Returns:
            str: 项目成员列表键
        """
        return cls.generate_key(cls.PROJECT_PREFIX, "members", str(project_id))
    
    @classmethod
    def get_project_databases_key(cls, project_id: int) -> str:
        """
        生成项目数据库列表键
        
        Args:
            project_id: 项目ID
            
        Returns:
            str: 项目数据库列表键
        """
        return cls.generate_key(cls.PROJECT_PREFIX, "databases", str(project_id))
    
    # 数据库实例相关键生成方法
    @classmethod
    def get_database_info_key(cls, db_id: int) -> str:
        """
        生成数据库实例信息键
        
        Args:
            db_id: 数据库实例ID
            
        Returns:
            str: 数据库实例信息键
        """
        return cls.generate_key(cls.DATABASE_PREFIX, "info", str(db_id))
    
    @classmethod
    def get_database_schema_key(cls, db_id: int) -> str:
        """
        生成数据库模式键
        
        Args:
            db_id: 数据库实例ID
            
        Returns:
            str: 数据库模式键
        """
        return cls.generate_key(cls.DATABASE_PREFIX, "schema", str(db_id))
    
    # SQL执行相关键生成方法
    @classmethod
    def get_sql_result_key(cls, sql_hash: str) -> str:
        """
        生成SQL执行结果键
        
        Args:
            sql_hash: SQL语句的哈希值
            
        Returns:
            str: SQL执行结果键
        """
        return cls.generate_key(cls.SQL_PREFIX, "result", sql_hash)
    
    @classmethod
    def get_sql_template_key(cls, template_id: int) -> str:
        """
        生成SQL模板键
        
        Args:
            template_id: SQL模板ID
            
        Returns:
            str: SQL模板键
        """
        return cls.generate_key(cls.SQL_PREFIX, "template", str(template_id))
    
    # 通用缓存键生成方法
    @classmethod
    def get_cache_key(cls, resource_type: str, resource_id: Any) -> str:
        """
        生成通用缓存键
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            
        Returns:
            str: 通用缓存键
        """
        return cls.generate_key(cls.CACHE_PREFIX, resource_type, str(resource_id))
    
    @classmethod
    def get_api_response_key(cls, endpoint: str, params_hash: str) -> str:
        """
        生成API响应缓存键
        
        Args:
            endpoint: API端点
            params_hash: 参数哈希值
            
        Returns:
            str: API响应缓存键
        """
        return cls.generate_key(cls.API_PREFIX, endpoint, params_hash)
    
    # 系统配置相关键生成方法
    @classmethod
    def get_system_config_key(cls, config_name: str) -> str:
        """
        生成系统配置键
        
        Args:
            config_name: 配置名称
            
        Returns:
            str: 系统配置键
        """
        return cls.generate_key(cls.SYSTEM_PREFIX, cls.CONFIG_PREFIX, config_name)


# 导出全局键管理器实例
redis_key_manager = RedisKeyManager()
