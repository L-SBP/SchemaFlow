"""
测试各种违规类型是否能正确标记用户为异常

测试账号分配：
- user01: excessive_api_usage (API频率超限) - 通过快速发送请求触发
- user02: sql_injection_attempt (SQL注入尝试) - 手动插入违规记录
- user03: suspicious_query (可疑查询) - 手动插入违规记录
- user04: unauthorized_access_attempt (未授权访问) - 手动插入违规记录
- user05: ai_violation_content (AI内容违规) - 手动插入违规记录
- user06: frequent_remote_login (异地频繁登录) - 手动插入违规记录
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_db():
    """获取数据库会话"""
    from core.database import PsqlHelper
    from core.config import settings
    
    db_config = settings.db  # 使用 settings.db 而不是 config.database
    engine = PsqlHelper._get_async_engine(db_config)
    session = PsqlHelper._get_async_session(engine)
    return session, engine

async def reset_user_status(db: AsyncSession, username: str):
    """重置用户状态为 normal"""
    from models.user_account import UserAccount
    result = await db.execute(select(UserAccount).where(UserAccount.username == username))
    user = result.scalar_one_or_none()
    if user:
        user.status = 'normal'
        await db.commit()
        print(f"  [重置] {username} 状态已重置为 normal")
        return user
    else:
        print(f"  [错误] 用户 {username} 不存在")
        return None

async def check_user_status(db: AsyncSession, username: str) -> str:
    """检查用户状态"""
    from models.user_account import UserAccount
    result = await db.execute(select(UserAccount).where(UserAccount.username == username))
    user = result.scalar_one_or_none()
    return user.status if user else "NOT_FOUND"

async def test_violation_type(db: AsyncSession, username: str, event_type: str, description: str, risk_level: str = "HIGH"):
    """测试单个违规类型"""
    from models.user_account import UserAccount
    from core.security import ViolationLogger
    
    print(f"\n{'='*60}")
    print(f"测试用户: {username}")
    print(f"违规类型: {event_type}")
    print(f"描述: {description}")
    print(f"{'='*60}")
    
    # 1. 获取用户
    result = await db.execute(select(UserAccount).where(UserAccount.username == username))
    user = result.scalar_one_or_none()
    if not user:
        print(f"  [错误] 用户 {username} 不存在")
        return False
    
    # 2. 重置用户状态
    user.status = 'normal'
    await db.commit()
    print(f"  [步骤1] 重置用户状态: normal")
    
    # 3. 记录违规日志（这会自动触发标记为异常）
    print(f"  [步骤2] 记录违规日志...")
    violation = await ViolationLogger.log_violation(
        db=db,
        user_id=user.user_id,
        event_type=event_type,
        event_description=description,
        risk_level=risk_level,
        ip_address="192.168.1.100",
        auto_check_suspend=True  # 自动检查并标记
    )
    await db.commit()
    print(f"  [步骤2] 违规日志已记录，ID: {violation.violation_id}")
    
    # 4. 刷新用户状态
    await db.refresh(user)
    final_status = user.status
    
    # 5. 判断结果
    if final_status == 'suspended':
        print(f"  [结果] ✅ 成功！用户已被标记为异常 (suspended)")
        return True
    else:
        print(f"  [结果] ❌ 失败！用户状态仍为: {final_status}")
        return False

async def main():
    print("=" * 70)
    print("违规类型触发异常标记测试")
    print("=" * 70)
    
    db, engine = await get_db()
    
    # 定义测试用例
    test_cases = [
        # (用户名, 违规类型, 描述, 风险等级)
        ("user01", "excessive_api_usage", "API频率超限: 50请求/10秒", "MEDIUM"),
        ("user02", "sql_injection_attempt", "检测到SQL注入攻击: DROP TABLE users", "CRITICAL"),
        ("user03", "suspicious_query", "可疑查询: SELECT * FROM passwords", "HIGH"),
        ("user04", "unauthorized_access_attempt", "尝试访问未授权资源: /admin/users", "HIGH"),
        ("user05", "ai_violation_content", "AI生成内容包含敏感信息", "MEDIUM"),
        ("user06", "frequent_remote_login", "异地频繁登录: 北京→上海→广州 (1小时内)", "HIGH"),
    ]
    
    results = []
    
    try:
        for username, event_type, description, risk_level in test_cases:
            success = await test_violation_type(db, username, event_type, description, risk_level)
            results.append((username, event_type, success))
        
        # 打印汇总
        print("\n" + "=" * 70)
        print("测试结果汇总")
        print("=" * 70)
        print(f"{'用户名':<10} {'违规类型':<30} {'结果':<10}")
        print("-" * 70)
        
        passed = 0
        failed = 0
        for username, event_type, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{username:<10} {event_type:<30} {status:<10}")
            if success:
                passed += 1
            else:
                failed += 1
        
        print("-" * 70)
        print(f"总计: {len(results)} 项测试, {passed} 通过, {failed} 失败")
        
        # 验证数据库中的状态
        print("\n" + "=" * 70)
        print("数据库最终状态验证")
        print("=" * 70)
        for username, event_type, _ in results:
            status = await check_user_status(db, username)
            print(f"  {username}: {status}")
        
    finally:
        await db.close()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
