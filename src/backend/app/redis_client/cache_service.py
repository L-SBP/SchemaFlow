"""
统一缓存服务接口

提供标准化的缓存操作接口，支持各种类型的缓存数据操作
实现了缓存穿透、雪崩、击穿的防护机制
"""

from typing import Any, Callable, Optional, TypeVar, Generic
import asyncio
import hashlib
import json
from datetime import timedelta

from core.config import config
from core.log import log
from redis_client.redis import get_redis
from redis_client.redis_keys import redis_key_manager

T = TypeVar('T')

class CacheResult(Generic[T]):
    """
    缓存结果封装类
    """
    def __init__(self, data: Optional[T] = None, from_cache: bool = False, ttl: Optional[int] = None):
        self.data = data
        self.from_cache = from_cache
        self.ttl = ttl

class CacheService:
    """
    统一缓存服务类
    """
    
    # 默认缓存时间 (秒)
    DEFAULT_TTL = 300  # 5分钟
    # 长缓存时间 (秒)
    LONG_TTL = 3600    # 1小时
    # 短缓存时间 (秒)
    SHORT_TTL = 60     # 1分钟
    # 缓存穿透防护时间 (秒)
    PENETRATION_TTL = 30  # 30秒
    # 分布式锁默认超时时间 (秒)
    LOCK_DEFAULT_TTL = 10
    
    @classmethod
    async def get(cls, key: str, default: Any = None) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            Any: 缓存数据或默认值
        """
        redis = get_redis()
        if not redis:
            return default
        
        try:
            value = await redis.get(key)
            if value is None:
                return default
            
            # 尝试反序列化为JSON对象
            try:
                # 只有当值是字符串且看起来像JSON时才尝试反序列化
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                    return json.loads(value)
                return value
            except json.JSONDecodeError:
                # 不是JSON，返回原始值
                return value
        except Exception as e:
            log.error(f"获取缓存失败: {e}", exc_info=True)
            return default
    
    @classmethod
    async def set(cls, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒), 默认使用DEFAULT_TTL
            
        Returns:
            bool: 是否设置成功
        """
        redis = get_redis()
        if not redis:
            return False
        
        try:
            ttl = ttl or cls.DEFAULT_TTL
            
            # 序列化复杂对象为JSON
            if value is not None and not isinstance(value, (str, int, float, bool)):
                # 检查是否有model_dump方法（Pydantic模型）
                if hasattr(value, 'model_dump'):
                    value = value.model_dump()
                # 检查是否有dict方法
                elif hasattr(value, 'dict'):
                    value = value.dict()
                value = json.dumps(value, default=str)  # default=str 处理datetime等特殊类型
                
            await redis.set(key, value, ex=ttl)
            return True
        except Exception as e:
            log.error(f"设置缓存失败: {e}", exc_info=True)
            return False
    
    @classmethod
    async def delete(cls, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        redis = get_redis()
        if not redis:
            return False
        
        try:
            await redis.delete(key)
            return True
        except Exception as e:
            log.error(f"删除缓存失败: {e}", exc_info=True)
            return False
    
    @classmethod
    async def delete_pattern(cls, pattern: str) -> int:
        """
        根据模式删除缓存
        
        Args:
            pattern: 缓存键模式
            
        Returns:
            int: 删除的缓存数量
        """
        redis = get_redis()
        if not redis:
            return 0
        
        try:
            keys = await redis.keys(pattern)
            if keys:
                return await redis.delete(*keys)
            return 0
        except Exception as e:
            log.error(f"根据模式删除缓存失败: {e}", exc_info=True)
            return 0
    
    @classmethod
    async def exists(cls, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 缓存是否存在
        """
        redis = get_redis()
        if not redis:
            return False
        
        try:
            return await redis.exists(key) > 0
        except Exception as e:
            log.error(f"检查缓存存在失败: {e}", exc_info=True)
            return False
    
    @classmethod
    async def get_or_set(cls, key: str, func: Callable[..., T], ttl: Optional[int] = None, 
                        *args, **kwargs) -> CacheResult[T]:
        """
        获取缓存，如果不存在则执行函数并缓存结果
        实现了缓存穿透和击穿防护
        
        Args:
            key: 缓存键
            func: 获取数据的函数
            ttl: 过期时间(秒)
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            CacheResult: 缓存结果
        """
        # 尝试从缓存获取
        cached_value = await cls.get(key)
        if cached_value is not None:
            return CacheResult(data=cached_value, from_cache=True, ttl=ttl)
        
        # 缓存穿透防护: 如果函数返回None，也缓存一个空值，设置较短的TTL
        try:
            # 使用分布式锁防止缓存击穿
            lock_key = f"lock:{key}"
            lock_acquired = await cls._acquire_lock(lock_key)
            
            if lock_acquired:
                try:
                    # 再次检查缓存，防止锁竞争期间其他请求已设置缓存
                    cached_value = await cls.get(key)
                    if cached_value is not None:
                        return CacheResult(data=cached_value, from_cache=True, ttl=ttl)
                    
                    # 执行函数获取数据
                    data = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                    
                    if data is not None:
                        # 缓存正常数据，使用指定TTL
                        await cls.set(key, data, ttl)
                        return CacheResult(data=data, from_cache=False, ttl=ttl)
                    else:
                        # 缓存空值，防止缓存穿透
                        await cls.set(key, "", cls.PENETRATION_TTL)
                        return CacheResult(data=None, from_cache=False, ttl=cls.PENETRATION_TTL)
                finally:
                    # 释放锁
                    await cls._release_lock(lock_key)
            else:
                # 获取锁失败，等待一段时间后重试
                await asyncio.sleep(0.1)
                return await cls.get_or_set(key, func, ttl, *args, **kwargs)
        except Exception as e:
            log.error(f"get_or_set 缓存操作失败: {e}", exc_info=True)
            # 如果获取数据失败，返回默认值，不缓存
            return CacheResult(data=None, from_cache=False)
    
    @classmethod
    async def _acquire_lock(cls, key: str, ttl: int = LOCK_DEFAULT_TTL) -> bool:
        """
        获取分布式锁
        
        Args:
            key: 锁键
            ttl: 锁过期时间
            
        Returns:
            bool: 是否获取到锁
        """
        redis = get_redis()
        if not redis:
            return False
        
        try:
            # 使用SETNX实现分布式锁
            result = await redis.set(key, "1", nx=True, ex=ttl)
            return result is True
        except Exception as e:
            log.error(f"获取分布式锁失败: {e}", exc_info=True)
            return False
    
    @classmethod
    async def _release_lock(cls, key: str) -> bool:
        """
        释放分布式锁
        
        Args:
            key: 锁键
            
        Returns:
            bool: 是否释放成功
        """
        redis = get_redis()
        if not redis:
            return False
        
        try:
            await redis.delete(key)
            return True
        except Exception as e:
            log.error(f"释放分布式锁失败: {e}", exc_info=True)
            return False
    
    @classmethod
    async def hash_get(cls, key: str, field: str, default: Any = None) -> Optional[Any]:
        """
        获取哈希表字段值
        
        Args:
            key: 缓存键
            field: 字段名
            default: 默认值
            
        Returns:
            Any: 字段值或默认值
        """
        redis = get_redis()
        if not redis:
            return default
        
        try:
            value = await redis.hget(key, field)
            if value is None:
                return default
            
            # 尝试反序列化为JSON对象
            try:
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                    return json.loads(value)
                return value
            except json.JSONDecodeError:
                # 不是JSON，返回原始值
                return value
        except Exception as e:
            log.error(f"获取哈希表字段失败: {e}", exc_info=True)
            return default
    
    @classmethod
    async def hash_set(cls, key: str, field: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置哈希表字段值
        
        Args:
            key: 缓存键
            field: 字段名
            value: 字段值
            ttl: 过期时间(秒)
            
        Returns:
            bool: 是否设置成功
        """
        redis = get_redis()
        if not redis:
            return False
        
        try:
            # 序列化复杂对象为JSON
            if value is not None and not isinstance(value, (str, int, float, bool)):
                # 检查是否有model_dump方法（Pydantic模型）
                if hasattr(value, 'model_dump'):
                    value = value.model_dump()
                # 检查是否有dict方法
                elif hasattr(value, 'dict'):
                    value = value.dict()
                value = json.dumps(value, default=str)  # default=str 处理datetime等特殊类型
            
            await redis.hset(key, field, value)
            if ttl:
                await redis.expire(key, ttl)
            return True
        except Exception as e:
            log.error(f"设置哈希表字段失败: {e}", exc_info=True)
            return False
    
    @classmethod
    async def hash_delete(cls, key: str, field: str) -> bool:
        """
        删除哈希表字段
        
        Args:
            key: 缓存键
            field: 字段名
            
        Returns:
            bool: 是否删除成功
        """
        redis = get_redis()
        if not redis:
            return False
        
        try:
            await redis.hdel(key, field)
            return True
        except Exception as e:
            log.error(f"删除哈希表字段失败: {e}", exc_info=True)
            return False
    
    @classmethod
    def generate_cache_key(cls, prefix: str, *parts: Any) -> str:
        """
        生成统一格式的缓存键
        
        Args:
            prefix: 缓存键前缀
            *parts: 缓存键的各个部分
            
        Returns:
            str: 完整的缓存键
        """
        # 将所有部分转换为字符串
        str_parts = [str(part) for part in parts]
        # 使用redis_key_manager生成统一格式的键
        return redis_key_manager.generate_key(*str_parts, prefix=prefix)


# 导出全局缓存服务实例
cache_service = CacheService()
