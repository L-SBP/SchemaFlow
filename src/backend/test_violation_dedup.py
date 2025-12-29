"""
测试违规日志去重逻辑
验证同一用户同一类型的违规只显示最新的一条
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from models.user_account import UserAccount
from models.violation_log import ViolationLog
from crud.crud_admin_data import crud_admin_data
from core.database import Base


async def test_violation_deduplication():
    """测试违规日志去重"""
    
    print("\n" + "=" * 70)
    print("测试：同一用户同一类型违规只显示最新一条")
    print("=" * 70)
    
    # 创建测试数据库
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as db:
        # 创建测试用户
        user1 = UserAccount(
            username="test_user1",
            email="user1@example.com",
            password_hash="hashed",
            status="normal"
        )
        user2 = UserAccount(
            username="test_user2",
            email="user2@example.com",
            password_hash="hashed",
            status="normal"
        )
        db.add_all([user1, user2])
        await db.commit()
        await db.refresh(user1)
        await db.refresh(user2)
        
        print(f"\n✓ 创建测试用户:")
        print(f"  - {user1.username} (ID: {user1.user_id})")
        print(f"  - {user2.username} (ID: {user2.user_id})")
        
        # 创建测试违规日志
        print("\n" + "-" * 70)
        print("创建测试违规日志")
        print("-" * 70)
        
        now = datetime.now(timezone.utc)
        
        # user1 的多次登录失败记录（应该只显示最新的一条）
        violations = [
            ViolationLog(
                user_id=user1.user_id,
                event_type="multiple_failed_logins",
                event_description="第1次记录",
                risk_level="HIGH",
                ip_address="192.168.1.1",
                resolution_status="pending",
                created_at=now - timedelta(minutes=10)
            ),
            ViolationLog(
                user_id=user1.user_id,
                event_type="multiple_failed_logins",
                event_description="第2次记录",
                risk_level="HIGH",
                ip_address="192.168.1.1",
                resolution_status="pending",
                created_at=now - timedelta(minutes=5)
            ),
            ViolationLog(
                user_id=user1.user_id,
                event_type="multiple_failed_logins",
                event_description="第3次记录（最新）",
                risk_level="HIGH",
                ip_address="192.168.1.1",
                resolution_status="pending",
                created_at=now
            ),
            # user1 的API频率超限记录
            ViolationLog(
                user_id=user1.user_id,
                event_type="excessive_api_usage",
                event_description="API频率超限",
                risk_level="MEDIUM",
                ip_address="192.168.1.1",
                resolution_status="pending",
                created_at=now - timedelta(minutes=3)
            ),
            # user2 的多次登录失败记录
            ViolationLog(
                user_id=user2.user_id,
                event_type="multiple_failed_logins",
                event_description="user2的登录失败",
                risk_level="HIGH",
                ip_address="192.168.1.2",
                resolution_status="pending",
                created_at=now - timedelta(minutes=2)
            ),
        ]
        
        db.add_all(violations)
        await db.commit()
        
        print(f"\n✓ 创建了 {len(violations)} 条违规日志:")
        print(f"  - user1: 3条多次登录失败 + 1条API频率超限")
        print(f"  - user2: 1条多次登录失败")
        
        # 查询所有违规日志（不去重）
        print("\n" + "-" * 70)
        print("查询所有违规日志（不去重）")
        print("-" * 70)
        
        result = await db.execute(
            select(ViolationLog).order_by(ViolationLog.created_at.desc())
        )
        all_violations = result.scalars().all()
        
        print(f"\n总记录数: {len(all_violations)}")
        for v in all_violations:
            print(f"  - {v.event_type} | user_id={v.user_id} | {v.event_description}")
        
        # 使用去重查询
        print("\n" + "-" * 70)
        print("使用去重查询（同一用户同一类型只显示最新）")
        print("-" * 70)
        
        dedup_logs, total = await crud_admin_data.get_violation_logs(
            db=db,
            page=1,
            page_size=20,
            risk_level=None,
            resolution_status=None
        )
        
        print(f"\n去重后记录数: {len(dedup_logs)}")
        for log in dedup_logs:
            print(f"  - {log['event_type']} | user_id={log['user_id']} | {log['event_description']}")
        
        # 验证结果
        print("\n" + "=" * 70)
        print("验证结果")
        print("=" * 70)
        
        # 应该有3条记录：
        # 1. user1的最新多次登录失败
        # 2. user1的API频率超限
        # 3. user2的多次登录失败
        expected_count = 3
        
        if len(dedup_logs) == expected_count:
            print(f"✅ 测试通过：去重后有 {expected_count} 条记录")
            
            # 验证user1的多次登录失败是最新的那条
            user1_login_fail = [log for log in dedup_logs 
                               if log['user_id'] == user1.user_id 
                               and log['event_type'] == 'multiple_failed_logins']
            
            if len(user1_login_fail) == 1:
                if "最新" in user1_login_fail[0]['event_description']:
                    print("✅ user1的多次登录失败显示的是最新记录")
                else:
                    print(f"❌ user1的多次登录失败不是最新记录: {user1_login_fail[0]['event_description']}")
            else:
                print(f"❌ user1的多次登录失败记录数错误: {len(user1_login_fail)}")
            
            # 验证user1的API频率超限
            user1_api = [log for log in dedup_logs 
                        if log['user_id'] == user1.user_id 
                        and log['event_type'] == 'excessive_api_usage']
            
            if len(user1_api) == 1:
                print("✅ user1的API频率超限记录正常")
            else:
                print(f"❌ user1的API频率超限记录数错误: {len(user1_api)}")
            
            # 验证user2的记录
            user2_logs = [log for log in dedup_logs if log['user_id'] == user2.user_id]
            
            if len(user2_logs) == 1:
                print("✅ user2的记录正常")
            else:
                print(f"❌ user2的记录数错误: {len(user2_logs)}")
                
        else:
            print(f"❌ 测试失败：去重后有 {len(dedup_logs)} 条记录，预期 {expected_count} 条")
        
        print("=" * 70 + "\n")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_violation_deduplication())
