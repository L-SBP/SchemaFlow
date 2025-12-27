import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.redis_client.cache_service import cache_service
from app.redis_client.redis import init_redis, close_redis
from app.core.config import config

async def test_cache_basic():
    """测试基本的缓存操作"""
    print("=== 测试基本缓存操作 ===")
    
    # 设置缓存
    key = "test:basic:key"
    value = "test_value"
    success = await cache_service.set(key, value, ttl=30)
    print(f"设置缓存 {key} = {value}: {'成功' if success else '失败'}")
    
    # 获取缓存
    cached_value = await cache_service.get(key)
    print(f"获取缓存 {key}: {cached_value}")
    assert cached_value == value, f"获取的缓存值与设置的值不匹配: {cached_value} != {value}"
    
    # 检查缓存是否存在
    exists = await cache_service.exists(key)
    print(f"检查缓存 {key} 是否存在: {'存在' if exists else '不存在'}")
    assert exists, f"缓存 {key} 应该存在"
    
    # 删除缓存
    deleted = await cache_service.delete(key)
    print(f"删除缓存 {key}: {'成功' if deleted else '失败'}")
    
    # 再次检查缓存是否存在
    exists = await cache_service.exists(key)
    print(f"再次检查缓存 {key} 是否存在: {'存在' if exists else '不存在'}")
    assert not exists, f"缓存 {key} 应该不存在"
    
    print("基本缓存操作测试通过")

async def test_cache_complex_object():
    """测试复杂对象的缓存操作"""
    print("\n=== 测试复杂对象缓存操作 ===")
    
    # 测试字典
    key = "test:complex:dict"
    value = {"name": "test", "age": 18, "tags": ["a", "b", "c"]}
    success = await cache_service.set(key, value, ttl=30)
    print(f"设置字典缓存 {key} = {value}: {'成功' if success else '失败'}")
    
    cached_value = await cache_service.get(key)
    print(f"获取字典缓存 {key}: {cached_value}")
    assert cached_value == value, f"获取的字典缓存值与设置的值不匹配"
    
    await cache_service.delete(key)
    
    # 测试列表
    key = "test:complex:list"
    value = [1, 2, 3, 4, 5]
    success = await cache_service.set(key, value, ttl=30)
    print(f"设置列表缓存 {key} = {value}: {'成功' if success else '失败'}")
    
    cached_value = await cache_service.get(key)
    print(f"获取列表缓存 {key}: {cached_value}")
    assert cached_value == value, f"获取的列表缓存值与设置的值不匹配"
    
    await cache_service.delete(key)
    print("复杂对象缓存操作测试通过")

async def test_get_or_set():
    """测试get_or_set功能"""
    print("\n=== 测试get_or_set功能 ===")
    
    # 定义获取数据的函数
    async def fetch_data():
        print("执行fetch_data函数获取数据")
        return {"data": "fetched_data", "timestamp": "2023-12-27"}
    
    # 第一次调用，应该执行函数
    key = "test:get_or_set:key"
    result = await cache_service.get_or_set(key, fetch_data, ttl=30)
    print(f"第一次调用get_or_set结果: {result.data}, from_cache: {result.from_cache}")
    assert not result.from_cache, "第一次调用应该不来自缓存"
    
    # 第二次调用，应该从缓存获取
    result = await cache_service.get_or_set(key, fetch_data, ttl=30)
    print(f"第二次调用get_or_set结果: {result.data}, from_cache: {result.from_cache}")
    assert result.from_cache, "第二次调用应该来自缓存"
    
    await cache_service.delete(key)
    print("get_or_set功能测试通过")

async def test_cache_ttl():
    """测试缓存过期时间"""
    print("\n=== 测试缓存过期时间 ===")
    
    key = "test:ttl:key"
    value = "ttl_test_value"
    
    # 设置缓存，过期时间1秒
    success = await cache_service.set(key, value, ttl=1)
    print(f"设置缓存 {key} = {value}, ttl=1秒: {'成功' if success else '失败'}")
    
    # 立即获取，应该存在
    cached_value = await cache_service.get(key)
    print(f"立即获取缓存 {key}: {cached_value}")
    assert cached_value == value, "缓存应该存在"
    
    # 等待2秒
    print("等待2秒...")
    await asyncio.sleep(2)
    
    # 再次获取，应该不存在
    cached_value = await cache_service.get(key)
    print(f"2秒后获取缓存 {key}: {cached_value}")
    assert cached_value is None, "缓存应该已过期"
    
    print("缓存过期时间测试通过")

async def test_delete_pattern():
    """测试根据模式删除缓存"""
    print("\n=== 测试根据模式删除缓存 ===")
    
    # 设置多个相关缓存
    keys = ["test:pattern:key1", "test:pattern:key2", "test:pattern:key3"]
    values = ["value1", "value2", "value3"]
    
    for key, value in zip(keys, values):
        await cache_service.set(key, value, ttl=300)
        print(f"设置缓存 {key} = {value}")
    
    # 验证缓存存在
    for key in keys:
        value = await cache_service.get(key)
        assert value is not None, f"缓存 {key} 应该存在"
    
    # 根据模式删除缓存
    pattern = "test:pattern:*"
    deleted_count = await cache_service.delete_pattern(pattern)
    print(f"根据模式 {pattern} 删除缓存，删除了 {deleted_count} 个缓存")
    assert deleted_count == len(keys), f"应该删除 {len(keys)} 个缓存，实际删除了 {deleted_count} 个"
    
    # 验证缓存已删除
    for key in keys:
        value = await cache_service.get(key)
        assert value is None, f"缓存 {key} 应该已被删除"
    
    print("根据模式删除缓存测试通过")

async def main():
    """主测试函数"""
    print(f"测试Redis缓存服务，配置: {config.redis.host}:{config.redis.port}")
    
    try:
        # 初始化Redis连接
        await init_redis()
        
        # 运行所有测试
        await test_cache_basic()
        await test_cache_complex_object()
        await test_get_or_set()
        await test_cache_ttl()
        await test_delete_pattern()
        
        print("\n=== 所有测试通过！===\n")
    except Exception as e:
        print(f"\n=== 测试失败: {e} ===\n")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭Redis连接
        await close_redis()

if __name__ == "__main__":
    asyncio.run(main())
