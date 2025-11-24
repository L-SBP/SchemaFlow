# 业务异常基类
class BusinessException(Exception):
    code: int  # 对应 HTTP 状态码（方便后续转换）
    message: str  # 异常信息

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

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
        super().__init__(code=401, message="Could not validate credentials")

class UserStatusForbiddenException(BusinessException):
    """用户状态异常（禁止访问）"""
    def __init__(self, status: str):
        super().__init__(code=403, message=f"User account status is '{status}'")

class DatabaseOperationFailedException(BusinessException):
    """数据库操作失败"""
    def __init__(self, operation: str = "operation"):
        super().__init__(code=500, message=f"Database {operation} failed")

class PasswordInvalidException(BusinessException):
    """密码错误"""
    def __init__(self):
        super().__init__(code=401, message="Incorrect username or password")