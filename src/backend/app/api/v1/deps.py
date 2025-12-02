# backend/app/api/v1/deps.py (完整修正版本)

from typing import AsyncGenerator
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from core.deps import get_engine, get_db
from redis.redis import get_redis
from core.auth import get_current_active_user as get_user_id_from_token # 重命名以区分职责
from crud.crud_user_account import crud_user_account
from models.user_account import UserAccount
from schema.user import UserMe # 导入用户DTO


from core.deps import get_db

# ---------------------------------------------------------------------
# 2. 获取认证用户ID的依赖 (使用 core.auth 中的函数)
# ---------------------------------------------------------------------

async def get_current_user_id(token: str = Depends(get_user_id_from_token)) -> int:
    """
    依赖函数：验证 JWT Token 并返回 user_id
    """
    # get_user_id_from_token 负责解码和抛出 401 异常
    return token


# ---------------------------------------------------------------------
# 3. 获取当前活动用户对象依赖 (Router 实际使用的依赖)
# ---------------------------------------------------------------------
async def get_current_active_user(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> UserMe:
    """
    依赖函数：从数据库获取当前用户对象，并进行状态检查。
    """
    try:
        user_orm: UserAccount = await crud_user_account.get(db=db, user_id=user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database query failed.")

    if not user_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


    if user_orm.status != "normal":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User status forbidden")


    return UserMe.model_validate(user_orm)

async def get_rd():
    """
    获取redis的依赖
    """
    return get_redis()


async def get_current_admin_user(user: UserMe = Depends(get_current_active_user)) -> UserMe:
    """
    依赖函数：验证当前用户是否为管理员。
    """
    # 假设 UserMe DTO (或底层的 ORM) 包含 is_admin 字段
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation forbidden: Admin privileges required"
        )
    return user