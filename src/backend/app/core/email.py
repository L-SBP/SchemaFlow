import random
from email.header import Header
from email.mime.text import MIMEText

from aiosmtplib import SMTP

from core.config import config
from core.log import log
from core.redis import get_redis

def _generate_code(length: int = 6) -> str:
    """生成一个6位数的随机验证码"""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

def make_email_content(verify_code: str):
    """
    生成邮件内容
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
    异步向指定邮箱发送验证码
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
            f"verification:{to_email}",
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
    验证邮箱和验证码
    """
    try:
        redis = get_redis()
        if redis is None:
            raise ValueError("Redis is not initialized")
        stored_code = await redis.get(f"verification:{to_email}")
        if stored_code is None:
            return False
        return stored_code == code
    except ValueError as e:
        log.error(f"Value error in verify_code: {e}")
        return False
    except Exception as e:
        log.error(f"Unexpected error in verify_code: {e}")
        return False