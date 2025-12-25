"""
统一异常处理模块。

提供全局异常处理器，统一处理各种类型的异常并返回标准化响应。
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from .exceptions import BusinessException, AppException
from .log import log


async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """
    处理业务异常。
    
    Args:
        request (Request): HTTP请求对象
        exc (BusinessException): 业务异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.warning(f"BusinessException: {exc.message}", extra={"path": request.url.path, "method": request.method})
    return JSONResponse(
        status_code=exc.code,
        content={
            "status_code": exc.code,
            "detail": exc.message,
            "message": "业务处理失败"
        },
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
    log.error(f"AppException: {exc.detail}", extra={"path": request.url.path, "method": request.method}, exc_info=True)
    return JSONResponse(
        status_code=exc.code,
        content={
            "status_code": exc.code,
            "detail": exc.detail or "内部服务器错误",
            "message": exc.message or "系统处理失败"
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求参数验证异常。
    
    Args:
        request (Request): HTTP请求对象
        exc (RequestValidationError): 请求验证异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.warning(f"ValidationError: {exc.errors()}", extra={"path": request.url.path, "method": request.method})
    
    # 提取验证错误信息
    error_details = []
    for error in exc.errors():
        field = "".join([f"[{k}]" if isinstance(k, int) else f".{k}" for k in error["loc"]]).lstrip(".")
        error_details.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "detail": "; ".join(error_details),
            "message": "请求参数验证失败"
        },
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
    log.warning(f"PydanticValidationError: {exc.errors()}", extra={"path": request.url.path, "method": request.method})
    
    # 提取验证错误信息
    error_details = []
    for error in exc.errors():
        field = "".join([f"[{k}]" if isinstance(k, int) else f".{k}" for k in error["loc"]]).lstrip(".")
        error_details.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "detail": "; ".join(error_details),
            "message": "数据验证失败"
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    处理数据库操作异常。
    
    Args:
        request (Request): HTTP请求对象
        exc (SQLAlchemyError): SQLAlchemy数据库异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.error(f"SQLAlchemyError: {str(exc)}", extra={"path": request.url.path, "method": request.method}, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": "数据库操作失败",
            "message": "系统处理失败"
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理通用异常，作为兜底异常处理器。
    
    Args:
        request (Request): HTTP请求对象
        exc (Exception): 通用异常实例
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    log.error(f"UnexpectedException: {str(exc)}", extra={"path": request.url.path, "method": request.method}, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": "内部服务器错误",
            "message": "系统处理失败"
        },
    )
