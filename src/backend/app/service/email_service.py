"""
邮件服务。

发送并验证邮箱验证码，用于邮箱更新与注册流程；依赖核心邮件工具与异常定义。
"""
from datetime import datetime

from core.log import log
from core.email_utils import send_verify_email, verify_code
from core import exceptions

async def service_send_verification_code(email: str) -> None:
    """
    向指定邮箱发送验证码。

    Args:
        email (str): 接收验证码的邮箱地址。

    Raises:
        exceptions.SendVerificationCodeFailedException: 发送失败。
    """
    result = await send_verify_email(email)

    if not result:
        log.error(f"Failed to send verification code to {email}")
        raise exceptions.SendVerificationCodeFailedException()

async def service_verify_code(email: str, code: str) -> bool:
    """
    验证邮箱和验证码。

    Args:
        email (str): 邮箱地址。
        code (str): 验证码。

    Returns:
        bool: 验证结果，True 表示验证通过。

    Raises:
        exceptions.CodeInvalidException: 验证失败。
    """
    result = await verify_code(email, code)
    if result:
        log.info(f"Verified verification code {code} for {email}")
        return True
    log.error(f"Invalid verification code {code} for {email}")
    raise exceptions.CodeInvalidException()
