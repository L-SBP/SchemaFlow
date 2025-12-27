# backend/app/api/v1/deps.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.exceptions import ForbiddenException, ItemNotFoundException
from core.deps import get_db, oauth2_scheme # 从 core.deps 导入 oauth2_scheme
from core.auth import decode_jwt_token # 导入刚才纯净版的工具函数
from crud.crud_user_account import crud_user_account
from schema.user import UserMe
from redis_client.redis import get_redis
from redis_client.redis_keys import redis_key_manager
from core.log import log

# 1. 这一步只负责从 Header 拿 Token 字符串
def get_token_str(token: str = Depends(oauth2_scheme)) -> str:
    return token

# 2. 这一步负责解析 Token 拿到 ID
async def get_current_user_id(token: str = Depends(get_token_str)) -> int:
    # 增加 Redis 黑名单检查 (队友的逻辑)
    redis = get_redis()
    if redis:
        is_valid = await redis.get(redis_key_manager.get_token_key(token))
        if not is_valid:
            raise ForbiddenException(message="令牌已被撤销")
    
    # 解码
    return decode_jwt_token(token)

# 3. 这一步查数据库拿到用户对象
async def get_current_active_user(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> UserMe:
    user_orm = await crud_user_account.get(db, user_id)
    if not user_orm:
        raise ItemNotFoundException(message="用户未找到")
    if user_orm.status != "normal":
        raise ForbiddenException(message="用户未激活")
    return UserMe.model_validate(user_orm)


async def get_current_admin_user(user: UserMe = Depends(get_current_active_user)) -> UserMe:
    """
    依赖函数：验证当前用户是否为管理员。
    """
    # 假设 UserMe DTO (或底层的 ORM) 包含 is_admin 字段
    if not user.is_admin:
        raise ForbiddenException(message="操作禁止：需要管理员权限")
    return user