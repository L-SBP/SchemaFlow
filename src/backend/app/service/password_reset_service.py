"""密码重置服务（邮箱验证码）。

流程：
- 用户输入邮箱，请求发送验证码（若账号存在）
- 用户在登录页输入验证码 + 新密码完成重置

安全性：
- 对外避免用户枚举：邮箱不存在也视为成功
- Redis 存验证码（带 TTL），成功后一次性删除
"""

from __future__ import annotations

import random

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import config
from core.log import log
from core.auth import get_password_hash
from crud.crud_user_account import crud_user_account
from redis_client.redis import get_redis
from core import exceptions
from core.email_utils import send_password_reset_code_email


def _generate_code(length: int = 6) -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


async def _rate_limit(redis, key: str, limit: int, window_seconds: int) -> bool:
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
        return count <= limit
    except Exception as e:
        log.warning(f"Rate limit redis_client operation failed: {e}")
        return True


async def service_send_password_reset_code(db: AsyncSession, email: str, client_ip: str | None = None) -> None:
    """发送密码重置验证码：若邮箱存在则发邮件；无论如何不抛用户可见异常。"""

    redis = get_redis()
    if redis is None:
        log.error("Redis is not initialized")
        return

    email_norm = (email or "").strip().lower()
    if not email_norm:
        return

    # 基础限流（按 email 与 IP）
    window = 3600
    if not await _rate_limit(
        redis,
        key=f"pwdreset:rl:email:{email_norm}",
        limit=getattr(config, "password_reset_request_limit_per_email_per_hour", 3),
        window_seconds=window,
    ):
        log.warning(f"Password reset request rate-limited by email: {email_norm}")
        return

    if client_ip:
        if not await _rate_limit(
            redis,
            key=f"pwdreset:rl:ip:{client_ip}",
            limit=getattr(config, "password_reset_request_limit_per_ip_per_hour", 20),
            window_seconds=window,
        ):
            log.warning(f"Password reset request rate-limited by ip: {client_ip}")
            return

    user = await crud_user_account.get_by_email(db, email_norm)
    if not user:
        return

    verify_code = _generate_code(6)
    ttl = int(getattr(config.smtp, "expire_time_seconds", 600))
    redis_key = f"pwdreset:code:{email_norm}"

    try:
        await redis.setex(redis_key, ttl, verify_code)
    except Exception as e:
        log.error(f"Failed to save password reset code in redis_client: {e}")
        return

    expire_minutes = max(1, int(ttl / 60))
    ok = await send_password_reset_code_email(user.email, verify_code, expire_minutes=expire_minutes)
    if not ok:
        try:
            await redis.delete(redis_key)
        except Exception:
            pass
        log.error(f"Failed to send password reset code email to {user.email}")


async def service_reset_password_with_code(db: AsyncSession, email: str, verification_code: str, new_password: str) -> None:
    """校验邮箱验证码并更新密码。"""

    redis = get_redis()
    if redis is None:
        raise exceptions.RedisOperationFailedException("get")

    email_norm = (email or "").strip().lower()
    code = (verification_code or "").strip()
    if not email_norm:
        raise exceptions.ValidationException("email is required")
    if not code:
        raise exceptions.ValidationException("verification_code is required")

    redis_key = f"pwdreset:code:{email_norm}"
    stored_code = await redis.get(redis_key)
    if not stored_code or stored_code != code:
        raise exceptions.ValidationException("Invalid or expired code")

    # 一次性
    await redis.delete(redis_key)

    user = await crud_user_account.get_by_email(db, email_norm)
    if not user:
        # 防枚举：不暴露用户不存在（但此时一般也无法通过验证码校验）
        raise exceptions.ValidationException("Invalid or expired code")

    hashed = get_password_hash(new_password)
    await crud_user_account.update(db, user, password_hash=hashed)
