"""
安全检查和频率限制模块。

提供 Redis 频率限制、违规日志记录、黑名单管理等功能。
"""

# backend/app/core/security.py

import json
from datetime import datetime, timezone
from typing import Optional, Tuple
import redis_client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from core.log import log
from models.violation_log import ViolationLog
from models.user_account import UserAccount

# ============================================================================
# 1. Redis 频率限制（三击触发机制）
# ============================================================================

class RedisFrequencyLimiter:
    """
    基于 Redis 的频率限制器。
    
    使用三击触发机制：
    - 记录用户的请求频率
    - 如果在指定时间窗口内请求次数超过阈值，标记为风险状态
    """
    
    def __init__(self):
        """
        初始化 Redis 连接（使用全局 Redis 客户端）。
        """
        from redis_client.redis import get_redis
        self.redis_client = get_redis()
    
    def check_frequency(self, user_id: int, 
                       time_window: int = 10,  # 时间窗口（秒）
                       threshold: int = 20,     # 请求次数阈值
                       ) -> Tuple[bool, int]:
        """
        检查用户请求频率是否超限。
        
        Args:
            user_id: 用户ID
            time_window: 时间窗口（秒），默认 10 秒
            threshold: 阈值（请求次数），默认 20 次
            
        Returns:
            Tuple[bool, int]: (是否超限, 当前请求次数)
            - True 表示超限，用户应该被限制
            - 当前请求次数
        """
        if not self.redis_client:
            log.warning("Redis 不可用，跳过频率限制")
            return False, 0
        
        try:
            from redis_client.redis_keys import redis_key_manager
            key = redis_key_manager.get_frequency_limit_key(user_id)
            
            # INCR 操作：增加请求计数
            current_count = self.redis_client.incr(key)
            
            # 第一次请求时设置过期时间
            if current_count == 1:
                self.redis_client.expire(key, time_window)
            
            # 判断是否超限
            is_exceeded = current_count > threshold
            
            if is_exceeded:
                log.warning("用户 {} 请求频率超限: {}/{}", user_id, current_count, threshold)
            
            return is_exceeded, current_count
        
        except Exception as e:
            log.error("Redis 频率限制检查失败: {}", e)
            return False, 0
    
    def get_frequency(self, user_id: int) -> int:
        """
        获取用户当前请求频率。
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 当前请求次数
        """
        if not self.redis_client:
            return 0
        
        try:
            from redis_client.redis_keys import redis_key_manager
            key = redis_key_manager.get_frequency_limit_key(user_id)
            count = self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            log.error("获取用户频率失败: {}", e)
            return 0
    
    def reset_frequency(self, user_id: int) -> bool:
        """
        重置用户请求频率（管理员使用）。
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否成功重置
        """
        if not self.redis_client:
            return False
        
        try:
            from redis_client.redis_keys import redis_key_manager
            key = redis_key_manager.get_frequency_limit_key(user_id)
            self.redis_client.delete(key)
            log.info("已重置用户 {} 的请求频率", user_id)
            return True
        except Exception as e:
            log.error("重置用户频率失败: {}", e)
            return False


# ============================================================================
# 1.5 登录失败计数器（三次密码错误标记为异常）
# ============================================================================

class LoginFailureTracker:
    """
    登录失败追踪器。
    
    记录用户连续输错密码的次数，达到阈值后将用户标记为异常（suspended）。
    使用 Redis 存储计数，24小时后自动过期。
    """
    
    # 密码错误阈值
    MAX_FAILED_ATTEMPTS = 3
    # 计数过期时间（秒）- 24小时
    EXPIRE_SECONDS = 86400
    
    def __init__(self):
        """初始化 Redis 连接"""
        from redis_client.redis import get_redis
        self.redis_client = get_redis()
    
    async def record_failed_attempt(self, user_id: int) -> Tuple[int, bool]:
        """
        记录一次登录失败。
        
        Args:
            user_id: 用户ID
            
        Returns:
            Tuple[int, bool]: (当前失败次数, 是否达到阈值)
        """
        if not self.redis_client:
            log.warning("Redis 不可用，跳过登录失败计数")
            return 0, False
        
        try:
            from redis_client.redis_keys import redis_key_manager
            key = redis_key_manager.get_login_fail_count_key(user_id)
            
            # 增加计数 (aioredis 是异步的，需要 await)
            count = await self.redis_client.incr(key)
            
            # 第一次失败时设置过期时间
            if count == 1:
                await self.redis_client.expire(key, self.EXPIRE_SECONDS)
            
            # 判断是否达到阈值
            should_suspend = count >= self.MAX_FAILED_ATTEMPTS
            
            if should_suspend:
                log.warning("用户 {} 连续 {} 次输错密码，将被标记为异常", user_id, count)
            else:
                log.info("用户 {} 登录失败，当前失败次数: {}/{}", user_id, count, self.MAX_FAILED_ATTEMPTS)
            
            return count, should_suspend
        
        except Exception as e:
            log.error("记录登录失败次数失败: {}", e)
            return 0, False
    
    async def get_failed_count(self, user_id: int) -> int:
        """
        获取用户当前的登录失败次数。
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 当前失败次数
        """
        if not self.redis_client:
            return 0
        
        try:
            from redis_client.redis_keys import redis_key_manager
            key = redis_key_manager.get_login_fail_count_key(user_id)
            count = await self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            log.error("获取登录失败次数失败: {}", e)
            return 0
    
    async def reset_failed_count(self, user_id: int) -> bool:
        """
        重置用户的登录失败计数（登录成功后调用）。
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否成功重置
        """
        if not self.redis_client:
            return False
        
        try:
            from redis_client.redis_keys import redis_key_manager
            key = redis_key_manager.get_login_fail_count_key(user_id)
            await self.redis_client.delete(key)
            log.info("已重置用户 {} 的登录失败计数", user_id)
            return True
        except Exception as e:
            log.error("重置登录失败计数失败: {}", e)
            return False


# ============================================================================
# 2. 违规日志记录器
# ============================================================================

class ViolationLogger:
    """
    违规日志记录器。
    
    负责记录用户的违规行为（频率超限、SQL 注入、权限拒绝等）。
    """
    
    # 违规事件类型常量
    EVENT_EXCESSIVE_API_USAGE = "excessive_api_usage"
    EVENT_SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    EVENT_SUSPICIOUS_QUERY = "suspicious_query"
    EVENT_UNAUTHORIZED_ACCESS = "unauthorized_access_attempt"
    EVENT_MULTIPLE_FAILED_LOGINS = "multiple_failed_logins"
    EVENT_AI_VIOLATION = "ai_violation_content"
    EVENT_FREQUENT_REMOTE_LOGIN = "frequent_remote_login"
    
    # 风险等级常量
    RISK_LOW = "LOW"
    RISK_MEDIUM = "MEDIUM"
    RISK_HIGH = "HIGH"
    RISK_CRITICAL = "CRITICAL"
    
    @staticmethod
    async def log_violation(
        db: AsyncSession,
        user_id: int,
        event_type: str,
        event_description: str,
        risk_level: str = "MEDIUM",
        ip_address: str = "127.0.0.1",
        client_user_agent: Optional[str] = None,
        request_content: Optional[str] = None,
        auto_check_suspend: bool = True,
    ) -> ViolationLog:
        """
        记录一条违规日志。
        
        Args:
            db: 数据库会话
            user_id: 违规用户ID
            event_type: 事件类型
            event_description: 事件描述
            risk_level: 风险等级（默认 MEDIUM）
            ip_address: IP 地址
            client_user_agent: 客户端信息
            request_content: 原始请求内容
            auto_check_suspend: 是否自动检查并标记用户为异常（默认 True）
                               如果调用方已经手动处理了标记逻辑，应设为 False
            
        Returns:
            ViolationLog: 创建的违规日志记录
        """
        try:
            violation = ViolationLog(
                user_id=user_id,
                event_type=event_type,
                event_description=event_description,
                risk_level=risk_level,
                ip_address=ip_address,
                client_user_agent=client_user_agent,
                request_content=request_content,
                resolution_status="pending"  # 初始状态为未处理
            )
            
            db.add(violation)
            await db.flush()  # 立即写入数据库，以便获取 violation_id
            
            log.warning(
                f"记录违规日志: 用户={user_id}, 类型={event_type}, "
                f"风险={risk_level}, ID={violation.violation_id}"
            )
            
            # 任何违规记录都直接标记用户为异常（仅当 auto_check_suspend=True 时执行）
            if auto_check_suspend:
                from core.security import BlacklistManager
                reason = f"触发违规记录: {event_type} - {event_description}"
                success = await BlacklistManager.suspend_user(db, user_id, reason=reason)
                if success:
                    log.warning(f"用户 {user_id} 因违规行为被标记为异常: {reason}")
            
            return violation
        
        except Exception as e:
            log.error("记录违规日志失败: {}", e)
            raise
    
    @staticmethod
    async def get_violation_count(
        db: AsyncSession,
        user_id: int,
        time_hours: int = 24,
        event_types: Optional[list] = None
    ) -> int:
        """
        获取用户在指定时间段内的违规记录数。
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            time_hours: 时间范围（小时），默认 24 小时
            event_types: 指定事件类型列表，如果为 None 则统计所有类型
            
        Returns:
            int: 违规记录数
        """
        try:
            # 计算时间范围
            from sqlalchemy import and_
            from datetime import timedelta
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_hours)
            
            query = select(ViolationLog).where(
                and_(
                    ViolationLog.user_id == user_id,
                    ViolationLog.created_at >= cutoff_time,
                    ViolationLog.resolution_status == "pending"
                )
            )
            
            # 如果指定了事件类型，额外过滤
            if event_types:
                query = query.where(ViolationLog.event_type.in_(event_types))
            
            result = await db.execute(query)
            violations = result.scalars().all()
            
            return len(violations)
        
        except Exception as e:
            log.error("查询违规记录失败: {}", e)
            return 0


# ============================================================================
# 3. 黑名单管理器
# ============================================================================

class BlacklistManager:
    """
    黑名单管理器。
    
    负责自动检测违规用户并将其加入黑名单，以及管理员的黑名单操作。
    """
    
    # 自动封禁的阈值
    VIOLATION_THRESHOLD = 3  # 24小时内3次违规记录触发自动标记为异常
    
    @staticmethod
    async def auto_suspend_if_needed(
        db: AsyncSession,
        user_id: int,
        violation_logger: ViolationLogger = ViolationLogger()
    ) -> Tuple[bool, Optional[str]]:
        """
        检查用户是否应该被自动标记为异常（三击机制）。
        
        注意：系统只会将用户标记为 suspended（异常），真正的封禁（banned）需要管理员手动操作。
        
        触发条件：
        1. 频率超限（Redis 记录）
        2. 24小时内违规记录 ≥ 3 条
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            violation_logger: 违规日志记录器实例
            
        Returns:
            Tuple[bool, Optional[str]]: (是否被标记为异常, 原因)
        """
        try:
            # 获取违规记录数
            violation_count = await violation_logger.get_violation_count(
                db, user_id, time_hours=24
            )
            
            if violation_count >= BlacklistManager.VIOLATION_THRESHOLD:
                # 自动标记用户为异常状态（suspended）
                reason = f"24小时内违规记录达到 {violation_count} 条，系统自动标记为异常"
                success = await BlacklistManager.suspend_user(
                    db, user_id, reason=reason
                )
                
                if success:
                    log.warning("自动标记用户 {} 为异常: {}", user_id, reason)
                    return True, reason
            
            return False, None
        
        except Exception as e:
            log.error("自动异常标记检查失败: {}", e)
            return False, None
    
    @staticmethod
    async def suspend_user(
        db: AsyncSession,
        user_id: int,
        reason: str = "系统检测到异常行为"
    ) -> bool:
        """
        将用户标记为异常状态（suspended）。
        
        注意：这是系统自动操作，不是真正的封禁。用户可以联系管理员申诉。
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            reason: 异常原因
            
        Returns:
            bool: 是否成功标记
        """
        try:
            result = await db.execute(
                select(UserAccount).where(UserAccount.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                log.error("用户 {} 不存在", user_id)
                return False
            
            # 只有 normal 状态的用户才能被标记为 suspended
            if user.status != 'normal':
                log.info("用户 {} 状态为 {}，跳过自动标记", user_id, user.status)
                return False
            
            user.status = 'suspended'
            await db.commit()
            
            log.warning("用户 {} 已被系统标记为异常: {}", user_id, reason)
            return True
        
        except Exception as e:
            log.error("标记用户异常失败: {}", e)
            await db.rollback()
            return False
    
    @staticmethod
    async def ban_user(
        db: AsyncSession,
        user_id: int,
        reason: str = "违反服务条款",
        banned_by: int = 0  # 管理员ID，0 表示系统
    ) -> bool:
        """
        管理员手动封禁用户（设置 status='banned'）。
        
        注意：只有管理员才能执行真正的封禁操作。
        
        Args:
            db: 数据库会话
            user_id: 要封禁的用户ID
            reason: 封禁原因
            banned_by: 执行封禁的管理员ID
            
        Returns:
            bool: 是否成功封禁
        """
        try:
            result = await db.execute(
                select(UserAccount).where(UserAccount.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                log.error("用户 {} 不存在", user_id)
                return False
            
            # 更新用户状态为 banned
            user.status = 'banned'
            
            await db.commit()
            
            log.warning("管理员 {} 封禁了用户 {}: {}", banned_by, user_id, reason)
            return True
        
        except Exception as e:
            log.error("封禁用户失败: {}", e)
            await db.rollback()
            return False
    
    @staticmethod
    async def unban_user(
        db: AsyncSession,
        user_id: int,
        admin_id: int = 0
    ) -> bool:
        """
        管理员解封用户（设置 status='normal'）。
        
        可以解除 banned 和 suspended 状态。
        
        Args:
            db: 数据库会话
            user_id: 要解封的用户ID
            admin_id: 执行解封的管理员ID
            
        Returns:
            bool: 是否成功解封
        """
        try:
            result = await db.execute(
                select(UserAccount).where(UserAccount.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                log.error("用户 {} 不存在", user_id)
                return False
            
            if user.status == 'normal':
                log.info("用户 {} 状态已经是 normal", user_id)
                return True
            
            # 更新用户状态为 normal
            old_status = user.status
            user.status = 'normal'
            
            await db.commit()
            
            log.info("管理员 {} 解封了用户 {} (原状态: {})", admin_id, user_id, old_status)
            return True
        
        except Exception as e:
            log.error("解封用户失败: {}", e)
            await db.rollback()
            return False
    
    @staticmethod
    async def get_banned_users(db: AsyncSession, limit: int = 100) -> list:
        """
        获取所有被封禁的用户列表（status='banned'）。
        
        Args:
            db: 数据库会话
            limit: 返回的最大记录数
            
        Returns:
            list: 被封禁的用户列表
        """
        try:
            result = await db.execute(
                select(UserAccount)
                .where(UserAccount.status == 'banned')
                .limit(limit)
            )
            users = result.scalars().all()
            return users
        
        except Exception as e:
            log.error("获取被封禁用户列表失败: {}", e)
            return []
    
    @staticmethod
    async def get_suspended_users(db: AsyncSession, limit: int = 100) -> list:
        """
        获取所有被系统标记为异常的用户列表（status='suspended'）。
        
        Args:
            db: 数据库会话
            limit: 返回的最大记录数
            
        Returns:
            list: 异常用户列表
        """
        try:
            result = await db.execute(
                select(UserAccount)
                .where(UserAccount.status == 'suspended')
                .limit(limit)
            )
            users = result.scalars().all()
            return users
        
        except Exception as e:
            log.error("获取异常用户列表失败: {}", e)
            return []


# ============================================================================
# 4. 全局实例
# ============================================================================

# 创建全局的 Redis 频率限制器实例
freq_limiter = RedisFrequencyLimiter()

# 创建全局的登录失败追踪器实例
login_failure_tracker = LoginFailureTracker()
