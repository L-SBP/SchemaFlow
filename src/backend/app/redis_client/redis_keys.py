"""
Redis 键前缀管理系统

该模块提供统一的 Redis 键生成和管理功能，确保所有 Redis 键遵循一致的命名规范。
支持环境隔离、键分类和统一的键生成接口。
"""

from typing import Optional
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


# 导出全局键管理器实例
redis_key_manager = RedisKeyManager()
