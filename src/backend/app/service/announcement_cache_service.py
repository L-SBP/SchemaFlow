"""
公告缓存服务。

提供公告的 Redis 缓存功能，包括列表缓存、详情缓存和缓存更新。
"""

import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from models.system_announcement import SystemAnnouncement as Announcement
from redis.redis import get_redis
from core.log import log

# 缓存键前缀
ANNOUNCEMENT_LIST_KEY = "announcement:list:published"
ANNOUNCEMENT_DETAIL_KEY_PREFIX = "announcement:detail:"
# 缓存过期时间（秒）：1小时
CACHE_TTL = 3600

class AnnouncementCacheService:
    """公告缓存服务类。"""

    @staticmethod
    async def _get_redis():
        """获取Redis连接。"""
        redis_conn = get_redis()
        if not redis_conn:
            log.warning("Redis connection not available")
            return None
        return redis_conn

    @staticmethod
    async def get_list_from_cache(page: int, page_size: int) -> Optional[Tuple[int, List[Dict]]]:
        """
        从缓存获取公告列表。
        
        Args:
            page (int): 页码
            page_size (int): 每页数量
            
        Returns:
            Optional[Tuple[int, List[Dict]]]: (总数, 公告列表) 或 None
        """
        redis_conn = await AnnouncementCacheService._get_redis()
        if not redis_conn:
            return None
            
        cache_key = f"{ANNOUNCEMENT_LIST_KEY}:page_{page}:size_{page_size}"
        try:
            cached_data = await redis_conn.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                log.info(f"Cache hit for announcement list: {cache_key}")
                return data["total"], data["items"]
        except Exception as e:
            log.error(f"Error getting announcement list from cache: {e}")
        
        return None

    @staticmethod
    async def set_list_to_cache(page: int, page_size: int, total: int, items: List[Dict]) -> None:
        """
        设置公告列表到缓存。
        
        Args:
            page (int): 页码
            page_size (int): 每页数量
            total (int): 总数
            items (List[Dict]): 公告列表
        """
        redis_conn = await AnnouncementCacheService._get_redis()
        if not redis_conn:
            return
            
        cache_key = f"{ANNOUNCEMENT_LIST_KEY}:page_{page}:size_{page_size}"
        try:
            cache_data = {
                "total": total,
                "items": items
            }
            await redis_conn.setex(cache_key, CACHE_TTL, json.dumps(cache_data, default=str))
            log.info(f"Cache set for announcement list: {cache_key}")
        except Exception as e:
            log.error(f"Error setting announcement list to cache: {e}")

    @staticmethod
    async def get_detail_from_cache(announcement_id: int) -> Optional[Dict]:
        """
        从缓存获取公告详情。
        
        Args:
            announcement_id (int): 公告ID
            
        Returns:
            Optional[Dict]: 公告详情或 None
        """
        redis_conn = await AnnouncementCacheService._get_redis()
        if not redis_conn:
            return None
            
        cache_key = f"{ANNOUNCEMENT_DETAIL_KEY_PREFIX}{announcement_id}"
        try:
            cached_data = await redis_conn.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                log.info(f"Cache hit for announcement detail: {announcement_id}")
                return data
        except Exception as e:
            log.error(f"Error getting announcement detail from cache: {e}")
        
        return None

    @staticmethod
    async def set_detail_to_cache(announcement_id: int, announcement_data: Dict) -> None:
        """
        设置公告详情到缓存。
        
        Args:
            announcement_id (int): 公告ID
            announcement_data (Dict): 公告数据
        """
        redis_conn = await AnnouncementCacheService._get_redis()
        if not redis_conn:
            return
            
        cache_key = f"{ANNOUNCEMENT_DETAIL_KEY_PREFIX}{announcement_id}"
        try:
            await redis_conn.setex(cache_key, CACHE_TTL, json.dumps(announcement_data, default=str))
            log.info(f"Cache set for announcement detail: {announcement_id}")
        except Exception as e:
            log.error(f"Error setting announcement detail to cache: {e}")

    @staticmethod
    async def invalidate_list_cache() -> None:
        """
        清除公告列表缓存。
        当公告有新增、更新或删除时调用。
        """
        redis_conn = await AnnouncementCacheService._get_redis()
        if not redis_conn:
            return
            
        try:
            # 使用 SCAN 命令查找并删除所有公告列表缓存
            pattern = f"{ANNOUNCEMENT_LIST_KEY}:*"
            cursor = 0
            while True:
                cursor, keys = await redis_conn.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    await redis_conn.delete(*keys)
                    log.info(f"Deleted announcement list cache keys: {keys}")
                if cursor == 0:
                    break
            log.info("Announcement list cache invalidated")
        except Exception as e:
            log.error(f"Error invalidating announcement list cache: {e}")

    @staticmethod
    async def invalidate_detail_cache(announcement_id: int) -> None:
        """
        清除指定公告的详情缓存。
        
        Args:
            announcement_id (int): 公告ID
        """
        redis_conn = await AnnouncementCacheService._get_redis()
        if not redis_conn:
            return
            
        cache_key = f"{ANNOUNCEMENT_DETAIL_KEY_PREFIX}{announcement_id}"
        try:
            await redis_conn.delete(cache_key)
            log.info(f"Deleted announcement detail cache: {announcement_id}")
        except Exception as e:
            log.error(f"Error invalidating announcement detail cache: {e}")

    @staticmethod
    async def invalidate_all_announcement_cache() -> None:
        """
        清除所有公告相关缓存（列表和详情）。
        """
        redis_conn = await AnnouncementCacheService._get_redis()
        if not redis_conn:
            return
            
        try:
            # 清除列表缓存
            await AnnouncementCacheService.invalidate_list_cache()
            
            # 清除所有详情缓存
            pattern = f"{ANNOUNCEMENT_DETAIL_KEY_PREFIX}*"
            cursor = 0
            while True:
                cursor, keys = await redis_conn.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    await redis_conn.delete(*keys)
                    log.info(f"Deleted announcement detail cache keys: {keys}")
                if cursor == 0:
                    break
            log.info("All announcement cache invalidated")
        except Exception as e:
            log.error(f"Error invalidating all announcement cache: {e}")

    @staticmethod
    async def get_fresh_data_from_db(db: AsyncSession, page: int, page_size: int) -> Tuple[int, List[Dict]]:
        """
        从数据库获取最新的公告列表数据。
        
        Args:
            db (AsyncSession): 数据库会话
            page (int): 页码
            page_size (int): 每页数量
            
        Returns:
            Tuple[int, List[Dict]]: (总数, 公告列表)
        """
        try:
            # 查询总数
            count_query = select(func.count()).select_from(
                select(Announcement)
                .where(Announcement.status == "published")
                .subquery()
            )
            total = (await db.execute(count_query)).scalar() or 0

            # 查询分页数据
            query = (
                select(Announcement)
                .where(Announcement.status == "published")
                .order_by(Announcement.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            rows = (await db.execute(query)).scalars().all()

            # 转换为字典列表
            items = []
            for row in rows:
                item = {
                    "announcement_id": row.announcement_id,
                    "title": row.title,
                    "content": row.content,
                    "status": row.status,
                    "created_by": row.created_by,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
                items.append(item)

            return total, items
        except Exception as e:
            log.error(f"Error getting fresh data from database: {e}")
            return 0, []
