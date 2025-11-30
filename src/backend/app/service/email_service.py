# services/email_service.py
from datetime import datetime

from core.log import log
from core.email_utils import send_verify_email, verify_code
from core import exceptions

async def service_send_verification_code(email: str):
    """
    向指定邮箱发送验证码
    :param email: 接收验证码的邮箱地址
    """
    result = await send_verify_email(email)

    if not result:
        log.error(f"Failed to send verification code to {email}")
        raise exceptions.SendVerificationCodeFailedException()

async def service_verify_code(email: str, code: str) -> bool:
    """
    验证邮箱和验证码
    :param email: 邮箱地址
    :param code: 验证码
    :return: 验证结果，True表示验证通过
    """
    result = await verify_code(email, code)
    if result:
        log.info(f"Verified verification code {code} for {email}")
        return True
    log.error(f"Invalid verification code {code} for {email}")
    raise exceptions.CodeInvalidException()
