#!/usr/bin/env python3
"""
Redis缓存功能测试脚本

测试缓存服务的基本功能，包括：
1. 基本的set/get操作
2. get_or_set逻辑
3. 序列化和反序列化
4. 缓存过期
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.redis_client.redis import init_redis, get_redis
from app.redis_client.cache_service import CacheService

async def test_basic_set_get():
    """测试基本的set和get操作"""
    print("\n=== 测试基本的set和get操作 ===")
    
    # 初始化Redis客户端
    await init_redis()
    
    # 测试数据
    test_key = "test:cache:basic"
    test_value = "Hello, Redis!"
    
    # 设置缓存
    set_result = await CacheService.set(test_key, test_value)
    print(f"设置缓存结果: {set_result}")
    assert set_result is True, "设置缓存失败"
    
    # 获取缓存
    get_result = await CacheService.get(test_key)
    print(f"获取缓存结果: {get_result}")
    assert get_result == test_value, f"获取缓存失败，预期: {test_value}, 实际: {get_result}"
    
    # 删除缓存
    delete_result = await CacheService.delete(test_key)
    print(f"删除缓存结果: {delete_result}")
    assert delete_result is True, "删除缓存失败"
    
    # 验证缓存已删除
    get_result = await CacheService.get(test_key)
    print(f"删除后获取缓存结果: {get_result}")
    assert get_result is None, "缓存删除失败"
    
    print("✅ 基本的set和get操作测试通过")

async def test_complex_object():
    """测试复杂对象的序列化和反序列化"""
    print("\n=== 测试复杂对象的序列化和反序列化 ===")
    
    # 初始化Redis客户端
    await init_redis()
    
    # 测试数据 - 复杂对象
    test_key = "test:cache:complex"
    test_value = {
        "name": "测试用户",
        "age": 30,
        "email": "test@example.com",
        "roles": ["admin", "user"],
        "settings": {
            "theme": "dark",
            "notifications": True
        }
    }
    
    # 设置缓存
    set_result = await CacheService.set(test_key, test_value)
    print(f"设置复杂对象缓存结果: {set_result}")
    assert set_result is True, "设置复杂对象缓存失败"
    
    # 获取缓存
    get_result = await CacheService.get(test_key)
    print(f"获取复杂对象缓存结果: {get_result}")
    assert get_result == test_value, f"获取复杂对象缓存失败，预期: {test_value}, 实际: {get_result}"
    
    # 验证数据类型
    assert isinstance(get_result, dict), "获取的结果不是字典类型"
    assert isinstance(get_result["roles"], list), "嵌套的roles不是列表类型"
    assert isinstance(get_result["settings"], dict), "嵌套的settings不是字典类型"
    
    # 删除缓存
    await CacheService.delete(test_key)
    
    print("✅ 复杂对象的序列化和反序列化测试通过")

async def test_get_or_set():
    """测试get_or_set功能"""
    print("\n=== 测试get_or_set功能 ===")
    
    # 初始化Redis客户端
    await init_redis()
    
    # 测试数据
    test_key = "test:cache:get_or_set"
    test_value = "数据来自数据库"
    
    # 模拟从数据库获取数据的函数
    async def fetch_from_db():
        print("  模拟从数据库获取数据")
        await asyncio.sleep(0.1)  # 模拟数据库延迟
        return test_value
    
    # 第一次调用 - 缓存不存在，会调用fetch_from_db
    result = await CacheService.get_or_set(test_key, fetch_from_db, ttl=10)
    print(f"第一次调用结果: {result.data}, 来自缓存: {result.from_cache}")
    assert result.data == test_value, "第一次调用结果不正确"
    assert result.from_cache is False, "第一次调用应该来自数据库，而不是缓存"
    
    # 第二次调用 - 缓存已存在，不会调用fetch_from_db
    result = await CacheService.get_or_set(test_key, fetch_from_db, ttl=10)
    print(f"第二次调用结果: {result.data}, 来自缓存: {result.from_cache}")
    assert result.data == test_value, "第二次调用结果不正确"
    assert result.from_cache is True, "第二次调用应该来自缓存"
    
    # 删除缓存
    await CacheService.delete(test_key)
    
    print("✅ get_or_set功能测试通过")

async def test_cache_ttl():
    """测试缓存过期功能"""
    print("\n=== 测试缓存过期功能 ===")
    
    # 初始化Redis客户端
    await init_redis()
    
    # 测试数据
    test_key = "test:cache:ttl"
    test_value = "临时数据"
    
    # 设置缓存，TTL为1秒
    set_result = await CacheService.set(test_key, test_value, ttl=1)
    print(f"设置缓存结果: {set_result}")
    assert set_result is True, "设置缓存失败"
    
    # 获取缓存 - 应该存在
    get_result = await CacheService.get(test_key)
    print(f"设置后立即获取: {get_result}")
    assert get_result == test_value, "缓存设置后立即获取失败"
    
    # 等待2秒，缓存应该过期
    print("等待2秒，让缓存过期...")
    await asyncio.sleep(2)
    
    # 获取缓存 - 应该不存在
    get_result = await CacheService.get(test_key)
    print(f"过期后获取: {get_result}")
    assert get_result is None, "缓存过期功能失败"
    
    print("✅ 缓存过期功能测试通过")

async def main():
    """运行所有测试"""
    print("开始Redis缓存功能测试")
    
    try:
        # 运行所有测试
        await test_basic_set_get()
        await test_complex_object()
        await test_get_or_set()
        await test_cache_ttl()
        
        print("\n🎉 所有测试通过！")
        return 0
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
