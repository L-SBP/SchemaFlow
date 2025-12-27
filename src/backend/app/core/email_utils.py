"""
邮件工具模块。

提供邮件内容生成、验证码生成、邮件发送及验证功能。
"""

# backend/app/core/email_utils.py

import random
from email.header import Header
from email.mime.text import MIMEText

from aiosmtplib import SMTP

from core.config import config
from core.log import log
from redis_client.redis import get_redis
from redis_client.redis_keys import redis_key_manager

def _generate_code(length: int = 6) -> str:
    """
    生成指定长度的随机数字验证码。

    Args:
        length (int): 验证码长度，默认6位。

    Returns:
        str: 随机生成的数字字符串。
    """
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

def make_email_content(verify_code: str):
    """
    生成包含验证码的 HTML 邮件内容。

    Args:
        verify_code (str): 验证码。

    Returns:
        str: HTML 格式的邮件内容字符串。
    """
    email_content = f"""
        <html>
            <body>
                <h3>亲爱的用户：</h3>
                <p>你正在进行邮箱验证操作，你的验证码为：</p>
                <p style="font-size: 20px; color: #1890ff; font-weight: bold;">{verify_code}</p>
                <p>验证码有效期为 {config.smtp.expire_time_seconds / 60} 分钟，请尽快完成验证。</p>
                <p>若你未发起此操作，请忽略本邮件，感谢你的使用！</p>
            </body>
        </html>
        """
    return email_content

async def send_verify_email(to_email: str, subject: str = "【auto_db_deployment】邮箱验证码"):
    """
    异步向指定邮箱发送验证码。

    生成验证码，发送邮件，并将验证码存储到 Redis 中。

    Args:
        to_email (str): 接收者邮箱地址。
        subject (str): 邮件主题。

    Returns:
        bool: 发送成功返回 True，失败返回 False。
    """
    verify_code = _generate_code()
    log.info(f"Generated verification code {verify_code} for {to_email}")

    email_content = make_email_content(verify_code)
    msg = MIMEText(email_content, "html", "utf-8")
    msg["From"] = config.smtp.sender
    msg["To"] = to_email
    msg["Subject"] = Header(subject, "utf-8")

    log.info(f"Email From: {msg['From']}, To: {msg['To']}, Subject: {msg['Subject']}")

    try:
        redis = get_redis()
        if redis is None:
            raise ValueError("Redis is not initialized")

        async with SMTP(
            hostname=config.smtp.host,
            port=config.smtp.port,
            username=config.smtp.sender,
            password=config.smtp.key,
            use_tls=True,
        ) as smtp:
            await smtp.send_message(
                msg,
                sender=config.smtp.sender,
                recipients=[to_email],
            )
            log.info(f"Sent verification code {verify_code} to {to_email}")

        await redis.setex(
            redis_key_manager.get_verification_key(to_email),
            config.smtp.expire_time_seconds,
            verify_code,
        )
        return True
    except ValueError as e:
        log.error(f"Value error in send_verify_email: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error in send_verify_email: {e}")
        return False

async def verify_code(to_email: str, code: str) -> bool:
    """
    验证邮箱和验证码是否匹配。

    从 Redis 中获取存储的验证码进行比对。

    Args:
        to_email (str): 邮箱地址。
        code (str): 待验证的验证码。

    Returns:
        bool: 验证成功返回 True，失败或过期返回 False。
    """
    try:
        redis = get_redis()
        if redis is None:
            raise ValueError("Redis is not initialized")
        from redis_client.redis_keys import redis_key_manager
        stored_code = await redis.get(redis_key_manager.get_verification_key(to_email))
        if stored_code is None:
            return False
        return stored_code == code
    except ValueError as e:
        log.error(f"Value error in verify_code: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error in verify_code: {e}")
        return False


def make_password_reset_email_content(reset_url: str, expire_minutes: int) -> str:
    """生成包含密码重置链接的 HTML 邮件内容。"""
    return f"""
        <html>
            <body>
                <h3>亲爱的用户：</h3>
                <p>你正在进行密码重置操作，请点击下方链接设置新密码：</p>
                <p style=\"margin: 16px 0;\">
                    <a href=\"{reset_url}\" style=\"display:inline-block;padding:10px 16px;background:#1890ff;color:#fff;border-radius:6px;text-decoration:none;\">重置密码</a>
                </p>
                <p>如果按钮无法点击，请复制以下链接到浏览器打开：</p>
                <p style=\"word-break: break-all;\">{reset_url}</p>
                <p>该链接有效期为 {expire_minutes} 分钟，请尽快完成操作。</p>
                <p>若你未发起此操作，请忽略本邮件。</p>
            </body>
        </html>
        """


async def send_password_reset_email(
    to_email: str,
    reset_url: str,
    subject: str = "【AutoDB】密码重置",
    expire_minutes: int = 15,
) -> bool:
    """异步发送密码重置邮件（不写 Redis，由调用方负责 token 存储）。"""
    email_content = make_password_reset_email_content(reset_url, expire_minutes)
    msg = MIMEText(email_content, "html", "utf-8")
    msg["From"] = config.smtp.sender
    msg["To"] = to_email
    msg["Subject"] = Header(subject, "utf-8")

    try:
        async with SMTP(
            hostname=config.smtp.host,
            port=config.smtp.port,
            username=config.smtp.sender,
            password=config.smtp.key,
            use_tls=True,
        ) as smtp:
            await smtp.send_message(
                msg,
                sender=config.smtp.sender,
                recipients=[to_email],
            )
        log.info(f"Sent password reset email to {to_email}")
        return True
    except Exception as e:
        log.error(f"Unexpected error in send_password_reset_email: {e}")
        return False


def make_password_reset_code_email_content(verify_code: str, expire_minutes: int) -> str:
    """生成包含密码重置验证码的 HTML 邮件内容。"""
    return f"""
        <html>
            <body>
                <h3>亲爱的用户：</h3>
                <p>你正在进行密码重置操作，你的验证码为：</p>
                <p style=\"font-size: 20px; color: #1890ff; font-weight: bold;\">{verify_code}</p>
                <p>验证码有效期为 {expire_minutes} 分钟，请尽快完成操作。</p>
                <p>若你未发起此操作，请忽略本邮件。</p>
            </body>
        </html>
        """


async def send_password_reset_code_email(
    to_email: str,
    verify_code: str,
    subject: str = "【AutoDB】密码重置验证码",
    expire_minutes: int = 10,
) -> bool:
    """异步发送密码重置验证码邮件（不写 Redis，由调用方负责存储/校验）。"""
    email_content = make_password_reset_code_email_content(verify_code, expire_minutes)
    msg = MIMEText(email_content, "html", "utf-8")
    msg["From"] = config.smtp.sender
    msg["To"] = to_email
    msg["Subject"] = Header(subject, "utf-8")

    try:
        async with SMTP(
            hostname=config.smtp.host,
            port=config.smtp.port,
            username=config.smtp.sender,
            password=config.smtp.key,
            use_tls=True,
        ) as smtp:
            await smtp.send_message(
                msg,
                sender=config.smtp.sender,
                recipients=[to_email],
            )
        log.info(f"Sent password reset code email to {to_email}")
        return True
    except Exception as e:
        log.error(f"Unexpected error in send_password_reset_code_email: {e}")
        return False
