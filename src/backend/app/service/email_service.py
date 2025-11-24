# services/email_service.py
import random
from datetime import datetime, timedelta

from core.log import log

# 模拟的验证码缓存
_code_cache = {}

def _generate_code(length: int = 6) -> str:
    """生成一个6位数的随机验证码"""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

async def send_verification_code(email: str) -> bool:
    """
    (模拟) 向指定邮箱发送验证码
    """
    code = _generate_code()
    expiry = datetime.now() + timedelta(minutes=5)

    # 存储到模拟缓存中
    _code_cache[email] = (code, expiry)
    log.info(f"Sent verification code {code} to {email} at {expiry}")

    # 关键：在终端打印验证码，方便你测试
    print(f"--- MOCK EMAIL SERVICE ---")
    print(f"To: {email}")
    print(f"Subject: Your verification code")
    print(f"Body: Your code is {code}")
    print(f"--------------------------")

    return True

async def verify_code(email: str, code: str) -> bool:
    """
    (模拟) 验证邮箱和验证码
    """
    if email not in _code_cache:
        return False

    cached_code, expiry = _code_cache[email]

    if datetime.now() > expiry:
        del _code_cache[email]
        return False

    if cached_code == code:
        del _code_cache[email]
        return True

    return False