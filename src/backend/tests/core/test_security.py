"""
安全模块单元测试。

测试 Redis 频率限制、违规日志记录、黑名单管理等功能。
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import (
    RedisFrequencyLimiter, 
    ViolationLogger, 
    BlacklistManager
)
from app.models.user_account import UserAccount
from app.models.violation_log import ViolationLog


# ============================================================================
# Redis 频率限制器测试
# ============================================================================

class TestRedisFrequencyLimiter:
    """测试 RedisFrequencyLimiter 类"""
    
    def setup_method(self):
        """每个测试前初始化"""
        self.limiter = RedisFrequencyLimiter()
    
    def test_frequency_limiter_initializes(self):
        """测试频率限制器初始化"""
        assert self.limiter is not None
        assert self.limiter.redis_client is not None
    
    def test_first_request_not_exceeded(self):
        """测试第一个请求不超限"""
        is_exceeded, count = self.limiter.check_frequency(
            user_id=9999,  # 使用不存在的用户ID避免冲突
            time_window=10,
            threshold=20
        )
        assert not is_exceeded
        assert count == 1
    
    def test_requests_below_threshold(self):
        """测试请求数在阈值以下"""
        user_id = 9998
        for i in range(1, 20):  # 发送19个请求
            is_exceeded, count = self.limiter.check_frequency(
                user_id=user_id,
                time_window=10,
                threshold=20
            )
            assert not is_exceeded
            assert count == i
    
    def test_threshold_boundary(self):
        """测试阈值边界 (第20个请求应该正常，第21个超限)"""
        user_id = 9997
        
        # 第20个请求应该正常
        is_exceeded, count = self.limiter.check_frequency(
            user_id=user_id,
            time_window=10,
            threshold=20
        )
        for _ in range(19):
            is_exceeded, count = self.limiter.check_frequency(
                user_id=user_id,
                time_window=10,
                threshold=20
            )
        assert count == 20
        assert not is_exceeded
        
        # 第21个请求超限
        is_exceeded, count = self.limiter.check_frequency(
            user_id=user_id,
            time_window=10,
            threshold=20
        )
        assert count == 21
        assert is_exceeded
    
    def test_redis_key_format(self):
        """测试 Redis 键格式是否正确"""
        user_id = 9996
        self.limiter.check_frequency(user_id=user_id)
        
        # 验证 Redis 中的键
        if self.limiter.redis_client:
            key = f"user:freq:{user_id}"
            value = self.limiter.redis_client.get(key)
            assert value is not None
            assert int(value) >= 1
    
    def teardown_method(self):
        """清理：删除测试数据"""
        if self.limiter.redis_client:
            for i in range(9996, 10000):
                key = f"user:freq:{i}"
                self.limiter.redis_client.delete(key)


# ============================================================================
# 违规日志记录器测试
# ============================================================================

@pytest.mark.asyncio
class TestViolationLogger:
    """测试 ViolationLogger 类"""
    
    @pytest.fixture
    async def test_user(self, db: AsyncSession):
        """创建测试用户"""
        user = UserAccount(
            username=f"test_user_{datetime.now().timestamp()}",
            email=f"test_{datetime.now().timestamp()}@example.com",
            password_hash="hashed_password"
        )
        db.add(user)
        await db.flush()
        return user
    
    async def test_log_violation_creates_record(self, db: AsyncSession, test_user):
        """测试记录违规日志"""
        violation = await ViolationLogger.log_violation(
            db=db,
            user_id=test_user.user_id,
            event_type=ViolationLogger.EVENT_EXCESSIVE_API_USAGE,
            event_description="Excessive API usage detected",
            risk_level=ViolationLogger.RISK_MEDIUM,
            ip_address="192.168.1.1",
            client_user_agent="Mozilla/5.0"
        )
        
        assert violation is not None
        assert violation.user_id == test_user.user_id
        assert violation.event_type == ViolationLogger.EVENT_EXCESSIVE_API_USAGE
        assert violation.resolution_status == "pending"
    
    async def test_log_multiple_violations(self, db: AsyncSession, test_user):
        """测试记录多条违规日志"""
        for i in range(3):
            violation = await ViolationLogger.log_violation(
                db=db,
                user_id=test_user.user_id,
                event_type=ViolationLogger.EVENT_SUSPICIOUS_QUERY,
                event_description=f"Suspicious query #{i+1}",
                risk_level=ViolationLogger.RISK_HIGH,
                ip_address="192.168.1.1",
                client_user_agent="Mozilla/5.0"
            )
            assert violation.violation_id is not None
    
    async def test_get_violation_count_24h(self, db: AsyncSession, test_user):
        """测试获取24小时内的违规记录数"""
        # 记录3条新的违规日志
        for i in range(3):
            await ViolationLogger.log_violation(
                db=db,
                user_id=test_user.user_id,
                event_type=ViolationLogger.EVENT_EXCESSIVE_API_USAGE,
                event_description=f"API usage #{i+1}",
                risk_level=ViolationLogger.RISK_LOW,
                ip_address="192.168.1.1",
                client_user_agent="test"
            )
        
        # 获取24小时内的计数
        count = await ViolationLogger.get_violation_count(
            db=db,
            user_id=test_user.user_id,
            time_hours=24
        )
        
        assert count >= 3
    
    async def test_get_violation_count_by_type(self, db: AsyncSession, test_user):
        """测试按事件类型筛选的违规记录数"""
        # 记录不同类型的违规日志
        await ViolationLogger.log_violation(
            db=db,
            user_id=test_user.user_id,
            event_type=ViolationLogger.EVENT_EXCESSIVE_API_USAGE,
            event_description="API usage",
            risk_level=ViolationLogger.RISK_MEDIUM,
            ip_address="192.168.1.1",
            client_user_agent="test"
        )
        
        await ViolationLogger.log_violation(
            db=db,
            user_id=test_user.user_id,
            event_type=ViolationLogger.EVENT_SUSPICIOUS_QUERY,
            event_description="Suspicious query",
            risk_level=ViolationLogger.RISK_HIGH,
            ip_address="192.168.1.1",
            client_user_agent="test"
        )
        
        # 获取特定类型的计数
        count = await ViolationLogger.get_violation_count(
            db=db,
            user_id=test_user.user_id,
            time_hours=24,
            event_types=[ViolationLogger.EVENT_EXCESSIVE_API_USAGE]
        )
        
        assert count >= 1


# ============================================================================
# 黑名单管理器测试
# ============================================================================

@pytest.mark.asyncio
class TestBlacklistManager:
    """测试 BlacklistManager 类"""
    
    @pytest.fixture
    async def test_user(self, db: AsyncSession):
        """创建测试用户"""
        user = UserAccount(
            username=f"ban_test_{datetime.now().timestamp()}",
            email=f"ban_{datetime.now().timestamp()}@example.com",
            password_hash="hashed_password",
            is_active=True
        )
        db.add(user)
        await db.commit()
        return user
    
    async def test_ban_user_sets_is_active_false(self, db: AsyncSession, test_user):
        """测试封禁用户设置 is_active=False"""
        success = await BlacklistManager.ban_user(
            db=db,
            user_id=test_user.user_id,
            reason="Test ban reason",
            banned_by=1  # 管理员ID为1
        )
        
        assert success
        
        # 验证用户状态
        result = await db.execute(
            select(UserAccount).where(UserAccount.user_id == test_user.user_id)
        )
        user = result.scalar_one()
        assert user.is_active == False
        assert user.ban_reason == "Test ban reason"
        assert user.banned_at is not None
    
    async def test_unban_user_sets_is_active_true(self, db: AsyncSession, test_user):
        """测试解封用户设置 is_active=True"""
        # 先封禁
        await BlacklistManager.ban_user(
            db=db,
            user_id=test_user.user_id,
            reason="Test ban"
        )
        
        # 再解封
        success = await BlacklistManager.unban_user(
            db=db,
            user_id=test_user.user_id
        )
        
        assert success
        
        # 验证用户状态
        result = await db.execute(
            select(UserAccount).where(UserAccount.user_id == test_user.user_id)
        )
        user = result.scalar_one()
        assert user.is_active == True
        assert user.ban_reason is None
        assert user.banned_at is None
    
    async def test_auto_ban_if_needed_with_3_violations(self, db: AsyncSession, test_user):
        """测试三击机制：3条违规记录触发自动封禁"""
        # 记录3条违规日志
        for i in range(3):
            await ViolationLogger.log_violation(
                db=db,
                user_id=test_user.user_id,
                event_type=ViolationLogger.EVENT_EXCESSIVE_API_USAGE,
                event_description=f"Violation #{i+1}",
                risk_level=ViolationLogger.RISK_MEDIUM,
                ip_address="192.168.1.1",
                client_user_agent="test"
            )
        
        # 触发自动封禁检查
        is_banned, reason = await BlacklistManager.auto_ban_if_needed(
            db=db,
            user_id=test_user.user_id
        )
        
        assert is_banned
        assert "3" in reason
        
        # 验证用户已被封禁
        result = await db.execute(
            select(UserAccount).where(UserAccount.user_id == test_user.user_id)
        )
        user = result.scalar_one()
        assert user.is_active == False
    
    async def test_auto_ban_if_needed_with_2_violations(self, db: AsyncSession, test_user):
        """测试三击机制：2条违规记录不触发自动封禁"""
        # 记录2条违规日志
        for i in range(2):
            await ViolationLogger.log_violation(
                db=db,
                user_id=test_user.user_id,
                event_type=ViolationLogger.EVENT_SUSPICIOUS_QUERY,
                event_description=f"Violation #{i+1}",
                risk_level=ViolationLogger.RISK_LOW,
                ip_address="192.168.1.1",
                client_user_agent="test"
            )
        
        # 触发自动封禁检查
        is_banned, reason = await BlacklistManager.auto_ban_if_needed(
            db=db,
            user_id=test_user.user_id
        )
        
        assert not is_banned
        
        # 验证用户未被封禁
        result = await db.execute(
            select(UserAccount).where(UserAccount.user_id == test_user.user_id)
        )
        user = result.scalar_one()
        assert user.is_active == True
    
    async def test_auto_ban_ignores_old_violations(self, db: AsyncSession, test_user):
        """测试自动封禁只计算24小时内的违规记录"""
        # 手动创建一条超过24小时的违规日志
        old_violation = ViolationLog(
            user_id=test_user.user_id,
            event_type=ViolationLogger.EVENT_EXCESSIVE_API_USAGE,
            event_description="Old violation",
            risk_level=ViolationLogger.RISK_HIGH,
            ip_address="192.168.1.1",
            created_at=datetime.now(timezone.utc) - timedelta(hours=25),
            resolution_status="pending"
        )
        db.add(old_violation)
        
        # 记录2条新的违规日志（在24小时内）
        for i in range(2):
            await ViolationLogger.log_violation(
                db=db,
                user_id=test_user.user_id,
                event_type=ViolationLogger.EVENT_SUSPICIOUS_QUERY,
                event_description=f"Recent violation #{i+1}",
                risk_level=ViolationLogger.RISK_MEDIUM,
                ip_address="192.168.1.1",
                client_user_agent="test"
            )
        
        # 触发自动封禁检查
        is_banned, reason = await BlacklistManager.auto_ban_if_needed(
            db=db,
            user_id=test_user.user_id
        )
        
        # 应该不被封禁 (只有2条24小时内的记录)
        assert not is_banned
        
        result = await db.execute(
            select(UserAccount).where(UserAccount.user_id == test_user.user_id)
        )
        user = result.scalar_one()
        assert user.is_active == True
    
    async def test_get_banned_users_list(self, db: AsyncSession):
        """测试获取被封禁用户列表"""
        # 创建并封禁一个用户
        ban_user = UserAccount(
            username=f"banned_{datetime.now().timestamp()}",
            email=f"banned_{datetime.now().timestamp()}@example.com",
            password_hash="hashed",
            is_active=False,
            ban_reason="Test ban"
        )
        db.add(ban_user)
        await db.commit()
        
        # 获取被封禁用户列表
        banned_users = await BlacklistManager.get_banned_users(db, limit=100)
        
        assert len(banned_users) > 0
        assert any(u.user_id == ban_user.user_id for u in banned_users)


# ============================================================================
# 集成测试：完整三击流程
# ============================================================================

@pytest.mark.asyncio
class TestStrikeSystemIntegration:
    """测试完整的三击自动封禁流程"""
    
    @pytest.fixture
    async def strike_user(self, db: AsyncSession):
        """创建测试用户"""
        user = UserAccount(
            username=f"strike_test_{datetime.now().timestamp()}",
            email=f"strike_{datetime.now().timestamp()}@example.com",
            password_hash="hashed",
            is_active=True
        )
        db.add(user)
        await db.commit()
        return user
    
    async def test_complete_strike_system_flow(self, db: AsyncSession, strike_user):
        """
        测试完整的三击流程：
        1. 记录第1条违规日志 → 用户仍然活跃
        2. 记录第2条违规日志 → 用户仍然活跃
        3. 记录第3条违规日志 → 自动触发封禁
        4. 用户被标记为非活跃
        """
        
        # 步骤1：第一条违规
        await ViolationLogger.log_violation(
            db=db,
            user_id=strike_user.user_id,
            event_type=ViolationLogger.EVENT_EXCESSIVE_API_USAGE,
            event_description="Strike 1",
            risk_level=ViolationLogger.RISK_MEDIUM,
            ip_address="192.168.1.1",
            client_user_agent="test"
        )
        
        is_banned, _ = await BlacklistManager.auto_ban_if_needed(db, strike_user.user_id)
        assert not is_banned
        
        # 步骤2：第二条违规
        await ViolationLogger.log_violation(
            db=db,
            user_id=strike_user.user_id,
            event_type=ViolationLogger.EVENT_SUSPICIOUS_QUERY,
            event_description="Strike 2",
            risk_level=ViolationLogger.RISK_HIGH,
            ip_address="192.168.1.1",
            client_user_agent="test"
        )
        
        is_banned, _ = await BlacklistManager.auto_ban_if_needed(db, strike_user.user_id)
        assert not is_banned
        
        # 步骤3：第三条违规 → 自动封禁
        await ViolationLogger.log_violation(
            db=db,
            user_id=strike_user.user_id,
            event_type=ViolationLogger.EVENT_SQL_INJECTION_ATTEMPT,
            event_description="Strike 3",
            risk_level=ViolationLogger.RISK_CRITICAL,
            ip_address="192.168.1.1",
            client_user_agent="test"
        )
        
        is_banned, reason = await BlacklistManager.auto_ban_if_needed(db, strike_user.user_id)
        assert is_banned
        assert "3" in reason
        
        # 验证最终状态
        result = await db.execute(
            select(UserAccount).where(UserAccount.user_id == strike_user.user_id)
        )
        user = result.scalar_one()
        assert user.is_active == False
        assert "三击机制" in user.ban_reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
