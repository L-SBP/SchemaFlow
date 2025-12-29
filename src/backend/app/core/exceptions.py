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
    message: str = "内部错误" # 用户可读的异常信息
    detail: Optional[str] = None  # 开发者可见的详细错误

    def __init__(self, code: int, detail: Optional[str] = None):
        self.code = code
        self.detail = detail
        super().__init__(detail)

# 具体业务异常（按需定义）
class TokenInvalidException(BusinessException):
    """Token 无效/解析失败异常。"""
    def __init__(self):
        super().__init__(code=401, message="无法验证凭据")

class EmailHasBeenRegisteredException(BusinessException):
    """邮箱已被注册异常。"""
    def __init__(self):
        super().__init__(code=400, message="邮箱已被注册")

class UsernameHasBeenRegisteredException(BusinessException):
    """用户名已被注册异常。"""
    def __init__(self):
        super().__init__(code=400, message="用户名已被注册")

class SendVerificationCodeFailedException(BusinessException):
    """发送验证码失败异常。"""
    def __init__(self):
        super().__init__(code=500, message="发送验证码失败")

class CodeInvalidException(BusinessException):
    """验证码无效或已过期异常。"""
    def __init__(self):
        super().__init__(code=400, message="验证码无效或已过期")

class UserNotFoundException(BusinessException):
    """用户不存在异常。"""
    def __init__(self):
        super().__init__(code=401, message="用户名或密码不正确")

class PasswordMismatchException(BusinessException):
    """密码不匹配异常。"""
    def __init__(self):
        super().__init__(code=400, message="密码不匹配")

class UserStatusForbiddenException(BusinessException):
    """
    用户状态异常（禁止访问）。

    Attributes:
        user_id (int): 用户 ID。
    """
    user_id: int
    def __init__(self, status: str, user_id: int):
        if status == 'suspended':
            message = "账户已被锁定（登录失败次数过多），请联系管理员解锁"
        elif status == 'banned':
            message = "账户已被封禁，请联系管理员"
        else:
            message = f"用户账号状态异常 ({status})，请联系管理员"
        super().__init__(code=403, message=message)
        self.user_id = user_id
        self.user_id = user_id

class PasswordInvalidException(BusinessException):
    """
    密码错误异常。

    Attributes:
        user_id (int): 用户 ID。
        failed_attempts (int): 连续失败次数。
    """
    user_id: int
    failed_attempts: int
    def __init__(self, user_id: int, failed_attempts: int = 0):
        if failed_attempts >= 3:
            # suspended 只是标记异常，用户仍可登录，但会被管理员关注
            message = f"密码错误次数过多，账户已被标记为异常，请注意账户安全"
        elif failed_attempts > 0:
            message = f"用户名或密码不正确，还剩 {3 - failed_attempts} 次尝试机会"
        else:
            message = "用户名或密码不正确"
        super().__init__(code=401, message=message)
        self.user_id = user_id
        self.failed_attempts = failed_attempts

class ValidationException(BusinessException):
    """数据验证失败异常。"""
    def __init__(self, message: str = "数据验证失败"):
        super().__init__(code=400, message=message)

class EmailNotVerifiedException(BusinessException):
    """邮箱未验证异常。"""
    def __init__(self):
        super().__init__(code=400, message="邮箱未验证")

class UserAlreadyExistsException(BusinessException):
    """用户已存在异常。"""
    def __init__(self):
        super().__init__(code=400, message="用户已存在")

class OperationNotPermittedException(BusinessException):
    """操作不允许异常。"""
    def __init__(self, message: str = "操作不允许"):
        super().__init__(code=403, message=message)

class ForbiddenException(BusinessException):
    """禁止访问异常。"""
    def __init__(self, message: str = "禁止访问"):
        super().__init__(code=403, message=message)

class ItemNotFoundException(BusinessException):
    """资源未找到异常。"""
    def __init__(self, message: str = "资源未找到"):
        super().__init__(code=404, message=message)

class InvalidOperationException(BusinessException):
    """无效的操作异常。"""
    def __init__(self, message: str = "无效的操作"):
        super().__init__(code=400, message=message)

class SQLSecurityException(BusinessException):
    """SQL 安全异常。"""
    def __init__(self, message: str = "SQL安全异常"):
        super().__init__(code=500, message=message)

class DatabaseOperationFailedException(AppException):
    """数据库操作失败异常。"""
    def __init__(self, operation: str = "操作", ):
        super().__init__(code=500, detail=f"数据库 {operation} 失败")

class RedisOperationFailedException(AppException):
    """Redis 操作失败异常。"""
    def __init__(self, operation: str = "操作"):
        super().__init__(code=500, detail=f"Redis {operation} 失败")


class SQLOperationFailedException(AppException):
    """SQL 执行失败异常。"""
    def __init__(self, operation: str = "操作", detail: str = ""):
        if detail:
            super().__init__(code=500, detail=f"SQL {operation} 失败: {detail}")
        else:
            super().__init__(code=500, detail=f"SQL {operation} 失败")


class SQLConversionException(BusinessException):
    """SQL 转换异常。"""
    def __init__(self, message: str = "SQL转换失败"):
        super().__init__(code=500, message=message)
