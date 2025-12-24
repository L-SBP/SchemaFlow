"""
异常处理模块。

定义业务异常和应用异常基类，以及各种具体的业务异常类。
"""

# backend/app/core/exceptions.py

from typing import Optional


class BusinessException(Exception):
    """
    业务异常基类。

    所有业务逻辑相关的异常都应继承此类。

    Attributes:
        code (int): 对应 HTTP 状态码。
        message (str): 用户可读的异常信息。
    """
    code: int  # 对应 HTTP 状态码（方便后续转换）
    message: str  # 异常信息

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

class AppException(Exception):
    """
    应用级异常基类。

    用于处理系统内部错误、配置错误等非业务逻辑异常。

    Attributes:
        code (int): HTTP 状态码。
        message (str): 默认异常信息。
        detail (Optional[str]): 开发者可见的详细错误信息。
    """
    code: int  # HTTP状态码
    message: str = "Internal Error" # 用户可读的异常信息
    detail: Optional[str] = None  # 开发者可见的详细错误

    def __init__(self, code: int, detail: Optional[str] = None):
        self.code = code
        self.detail = detail
        super().__init__(detail)

# 具体业务异常（按需定义）
class TokenInvalidException(BusinessException):
    """Token 无效/解析失败异常。"""
    def __init__(self):
        super().__init__(code=401, message="Could not validate credentials")

class EmailHasBeenRegisteredException(BusinessException):
    """邮箱已被注册异常。"""
    def __init__(self):
        super().__init__(code=400, message="Email has been registered")

class UsernameHasBeenRegisteredException(BusinessException):
    """用户名已被注册异常。"""
    def __init__(self):
        super().__init__(code=400, message="Username has been registered")

class SendVerificationCodeFailedException(BusinessException):
    """发送验证码失败异常。"""
    def __init__(self):
        super().__init__(code=500, message="Failed to send verification code")

class CodeInvalidException(BusinessException):
    """验证码无效或已过期异常。"""
    def __init__(self):
        super().__init__(code=400, message="Invalid or expired code")

class UserNotFoundException(BusinessException):
    """用户不存在异常。"""
    def __init__(self):
        super().__init__(code=401, message="Incorrect username or password")

class PasswordMismatchException(BusinessException):
    """密码不匹配异常。"""
    def __init__(self):
        super().__init__(code=400, message="Password mismatch")

class UserStatusForbiddenException(BusinessException):
    """
    用户状态异常（禁止访问）。

    Attributes:
        user_id (int): 用户 ID。
    """
    user_id: int
    def __init__(self, status: str, user_id: int):
        super().__init__(code=403, message=f"User account status is '{status}'")
        self.user_id = user_id

class PasswordInvalidException(BusinessException):
    """
    密码错误异常。

    Attributes:
        user_id (int): 用户 ID。
    """
    user_id: int
    def __init__(self, user_id: int):
        super().__init__(code=401, message="Incorrect username or password")
        self.user_id = user_id

class ValidationException(BusinessException):
    """数据验证失败异常。"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(code=400, message=message)

class EmailNotVerifiedException(BusinessException):
    """邮箱未验证异常。"""
    def __init__(self):
        super().__init__(code=400, message="Email not verified")

class UserAlreadyExistsException(BusinessException):
    """用户已存在异常。"""
    def __init__(self):
        super().__init__(code=400, message="User already exists")

class OperationNotPermittedException(BusinessException):
    """操作不允许异常。"""
    def __init__(self, message: str = "Operation not permitted"):
        super().__init__(code=403, message=message)

class ForbiddenException(BusinessException):
    """禁止访问异常。"""
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(code=403, message=message)

class ItemNotFoundException(BusinessException):
    """资源未找到异常。"""
    def __init__(self, message: str = "Item not found"):
        super().__init__(code=404, message=message)

class InvalidOperationException(BusinessException):
    """无效的操作异常。"""
    def __init__(self, message: str = "Invalid operation"):
        super().__init__(code=400, message=message)

class SQLSecurityException(BusinessException):
    """SQL 安全异常。"""
    def __init__(self, message: str = "SQL security exception"):
        super().__init__(code=500, message=message)

class DatabaseOperationFailedException(AppException):
    """数据库操作失败异常。"""
    def __init__(self, operation: str = "operation", ):
        super().__init__(code=500, detail=f"Database {operation} failed")

class RedisOperationFailedException(AppException):
    """Redis 操作失败异常。"""
    def __init__(self, operation: str = "operation"):
        super().__init__(code=500, detail=f"Redis {operation} failed")


class SQLOperationFailedException(AppException):
    """SQL 执行失败异常。"""
    def __init__(self, operation: str = "operation", detail: str = ""):
        if detail:
            super().__init__(code=500, detail=f"SQL {operation} failed: {detail}")
        else:
            super().__init__(code=500, detail=f"SQL {operation} failed")
