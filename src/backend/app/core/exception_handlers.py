"""
统一异常处理模块。

提供全局异常处理器，统一处理各种类型的异常并返回标准化响应。
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

# 第三方库异常导入
import redis.exceptions as redis_exceptions
import jose.exceptions as jose_exceptions
import httpx
import aiohttp
import celery.exceptions as celery_exceptions

from .exceptions import BusinessException, AppException, SQLConversionException, UserNotFoundException, PasswordInvalidException
from .log import log
from schema.unified_response import UnifiedResponse


# 错误代码常量定义
class ErrorCodes:
    """错误代码常量类"""
    # 参数验证错误
    PARAM_VALIDATION_ERROR = 10001
    DATA_VALIDATION_ERROR = 10002
    
    # 数据库错误
    DATABASE_OPERATION_ERROR = 20001
    SQL_CONVERSION_ERROR = 20007
    
    # 系统内部错误
    SYSTEM_INTERNAL_ERROR = 20002
    IO_OPERATION_ERROR = 20003
    TIMEOUT_ERROR = 20004
    TYPE_ERROR = 20005
    VALUE_ERROR = 20006
    KEY_ATTRIBUTE_ERROR = 20009
    
    # 第三方服务错误
    REDIS_OPERATION_ERROR = 20008
    CELERY_TASK_ERROR = 20010
    HTTP_REQUEST_ERROR = 20011
    
    # 认证错误
    AUTHENTICATION_ERROR = 401


# ======================
# 自定义异常处理器
# ======================

async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """
    处理业务异常。
    
    Args:
        request (Request): HTTP请求对象
        exc (BusinessException): 业务异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.warning("BusinessException: {}", exc.message, extra={"path": request.url.path, "method": request.method})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UnifiedResponse.error(
            code=exc.code,
            message=exc.message,
            data=None
        ).dict()
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    处理应用级异常。
    
    Args:
        request (Request): HTTP请求对象
        exc (AppException): 应用级异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.error("AppException: {}", exc.detail, extra={"path": request.url.path, "method": request.method}, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UnifiedResponse.error(
            code=exc.code,
            message=exc.message or "系统处理失败",
            data=None
        ).dict()
    )


# ======================
# 验证异常处理器
# ======================

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求参数验证异常。
    
    Args:
        request (Request): HTTP请求对象
        exc (RequestValidationError): 请求验证异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    error_info = exc.errors()
    log.warning("ValidationError: {}", error_info, extra={"path": request.url.path, "method": request.method})
    
    # 提取验证错误信息
    error_details = []
    for error in exc.errors():
        msg = error['msg']
        if ', ' in msg:
            msg = msg.split(', ', 1)[1]
        error_details.append(f"{msg}")
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UnifiedResponse.error(
            code=ErrorCodes.PARAM_VALIDATION_ERROR,
            message=". ".join(error_details),
            data=None
        ).dict()
    )


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    处理Pydantic模型验证异常。
    
    Args:
        request (Request): HTTP请求对象
        exc (ValidationError): Pydantic验证异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    error_info = exc.errors()
    log.warning("PydanticValidationError: {}", error_info, extra={"path": request.url.path, "method": request.method})
    
    # 提取验证错误信息
    error_details = []
    for error in exc.errors():
        # 移除错误信息中的英文前缀，保留中文部分
        msg = error['msg']
        if ', ' in msg:
            msg = msg.split(', ', 1)[1]
        error_details.append(f"{msg}")
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UnifiedResponse.error(
            code=ErrorCodes.DATA_VALIDATION_ERROR,
            message=". ".join(error_details),
            data=None
        ).dict()
    )


# ======================
# 数据库异常处理器
# ======================

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    处理数据库操作异常。
    
    Args:
        request (Request): HTTP请求对象
        exc (SQLAlchemyError): SQLAlchemy数据库异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.error("SQLAlchemyError: {}", str(exc), extra={"path": request.url.path, "method": request.method}, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UnifiedResponse.error(
            code=ErrorCodes.DATABASE_OPERATION_ERROR,
            message="数据库操作失败",
            data=None
        ).dict()
    )


async def sql_conversion_exception_handler(request: Request, exc: SQLConversionException) -> JSONResponse:
    """
    处理SQL转换异常。
    
    Args:
        request (Request): HTTP请求对象
        exc (SQLConversionException): SQL转换异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.warning("SQLConversionException: {}", exc.message, extra={"path": request.url.path, "method": request.method})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UnifiedResponse.error(
            code=exc.code,
            message=exc.message,
            data=None
        ).dict()
    )


# ======================
# 内置异常处理器
# ======================

async def io_exception_handler(request: Request, exc: IOError | FileNotFoundError) -> JSONResponse:
    """
    处理IO异常，如文件操作失败等。
    
    Args:
        request (Request): HTTP请求对象
        exc (IOError | FileNotFoundError): IO异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    error_message = f"文件操作失败: {str(exc)}"
    log.error("IOError: {}", error_message, extra={"path": request.url.path, "method": request.method}, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UnifiedResponse.error(
            code=ErrorCodes.IO_OPERATION_ERROR,
            message=error_message,
            data=None
        ).dict()
    )


async def timeout_exception_handler(request: Request, exc: TimeoutError) -> JSONResponse:
    """
    处理超时异常，如网络请求超时等。
    
    Args:
        request (Request): HTTP请求对象
        exc (TimeoutError): 超时异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.error("TimeoutError: {}", str(exc), extra={"path": request.url.path, "method": request.method}, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UnifiedResponse.error(
            code=ErrorCodes.TIMEOUT_ERROR,
            message="请求超时，请稍后重试",
            data=None
        ).dict()
    )


async def type_exception_handler(request: Request, exc: TypeError) -> JSONResponse:
    """
    处理类型错误异常。
    
    Args:
        request (Request): HTTP请求对象
        exc (TypeError): 类型错误异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.error("TypeError: {}", str(exc), extra={"path": request.url.path, "method": request.method}, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UnifiedResponse.error(
            code=ErrorCodes.TYPE_ERROR,
            message="系统内部类型错误",
            data=None
        ).dict()
    )


async def value_exception_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    处理值错误异常。
    
    Args:
        request (Request): HTTP请求对象
        exc (ValueError): 值错误异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.error("ValueError: {}", str(exc), extra={"path": request.url.path, "method": request.method}, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UnifiedResponse.error(
            code=ErrorCodes.VALUE_ERROR,
            message="系统内部值错误",
            data=None
        ).dict()
    )


async def key_exception_handler(request: Request, exc: KeyError | AttributeError) -> JSONResponse:
    """
    处理键错误和属性错误异常。
    
    Args:
        request (Request): HTTP请求对象
        exc (KeyError | AttributeError): 键错误或属性错误异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.error("Key/AttributeError: {}", str(exc), extra={"path": request.url.path, "method": request.method}, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UnifiedResponse.error(
            code=ErrorCodes.KEY_ATTRIBUTE_ERROR,
            message="系统内部数据访问错误",
            data=None
        ).dict()
    )


# ======================
# 第三方库异常处理器
# ======================

async def jwt_exception_handler(request: Request, exc: jose_exceptions.JWTError) -> JSONResponse:
    """
    处理JWT相关异常。
    
    Args:
        request (Request): HTTP请求对象
        exc (jose_exceptions.JWTError): JWT异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.error("JWTError: {}", str(exc), extra={"path": request.url.path, "method": request.method}, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UnifiedResponse.error(
            code=ErrorCodes.AUTHENTICATION_ERROR,
            message="令牌无效或已过期",
            data=None
        ).dict()
    )


# ======================
# 兜底异常处理器
# ======================

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理通用异常，作为兜底异常处理器。
    
    Args:
        request (Request): HTTP请求对象
        exc (Exception): 通用异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.error("UnexpectedException: {}", str(exc), extra={"path": request.url.path, "method": request.method}, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=UnifiedResponse.error(
            code=ErrorCodes.SYSTEM_INTERNAL_ERROR,
            message="系统处理失败",
            data=None
        ).dict()
    )