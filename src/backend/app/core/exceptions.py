from typing import Optional


class BusinessException(Exception):
    """业务异常基类"""
    code: int  # 对应 HTTP 状态码（方便后续转换）
    message: str  # 异常信息

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

class AppException(Exception):
    """应用级异常基类"""
    code: int  # HTTP状态码
    message: str = "Internal Error" # 用户可读的异常信息
    detail: Optional[str] = None  # 开发者可见的详细错误

    def __init__(self, code: int, detail: Optional[str] = None):
        self.code = code
        self.detail = detail
        super().__init__(detail)

# 具体业务异常（按需定义）
class TokenInvalidException(BusinessException):
    """Token 无效/解析失败"""
    def __init__(self):
        super().__init__(code=401, message="Could not validate credentials")

class EmailHasBeenRegisteredException(BusinessException):
    """邮箱已被注册"""
    def __init__(self):
        super().__init__(code=400, message="Email has been registered")

class UsernameHasBeenRegisteredException(BusinessException):
    """用户名已被注册"""
    def __init__(self):
        super().__init__(code=400, message="Username has been registered")

class SendVerificationCodeFailedException(BusinessException):
    """发送验证码失败"""
    def __init__(self):
        super().__init__(code=500, message="Failed to send verification code")

class CodeInvalidException(BusinessException):
    """验证码无效或已过期"""
    def __init__(self):
        super().__init__(code=400, message="Invalid or expired code")

class UserNotFoundException(BusinessException):
    """用户不存在"""
    def __init__(self):
        super().__init__(code=401, message="Incorrect username or password")

class PasswordMismatchException(BusinessException):
    """密码不匹配"""
    def __init__(self):
        super().__init__(code=400, message="Password mismatch")

class UserStatusForbiddenException(BusinessException):
    """用户状态异常（禁止访问）"""
    def __init__(self, status: str):
        super().__init__(code=403, message=f"User account status is '{status}'")

class PasswordInvalidException(BusinessException):
    """密码错误"""
    def __init__(self):
        super().__init__(code=401, message="Incorrect username or password")

class ValidationException(BusinessException):
    """数据验证失败"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(code=400, message=message)

class EmailNotVerifiedException(BusinessException):
    """邮箱未验证"""
    def __init__(self):
        super().__init__(code=400, message="Email not verified")

class UserAlreadyExistsException(BusinessException):
    """用户已存在"""
    def __init__(self):
        super().__init__(code=400, message="User already exists")

class OperationNotPermittedException(BusinessException):
    """操作不允许"""
    def __init__(self, message: str = "Operation not permitted"):
        super().__init__(code=403, message=message)

class DatabaseOperationFailedException(AppException):
    """数据库操作失败"""
    def __init__(self, operation: str = "operation", ):
        super().__init__(code=500, detail=f"Database {operation} failed")

class RedisOperationFailedException(AppException):
    """Redis 操作失败"""
    def __init__(self, operation: str = "operation"):
        super().__init__(code=500, detail=f"Redis {operation} failed")


class ItemNotFoundException(BusinessException):
    """资源未找到"""
    def __init__(self, message: str = "Item not found"):
        super().__init__(code=404, message=message)