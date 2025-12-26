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
from schema.unified_response import UnifiedResponse


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
    response = UnifiedResponse.error(
        code=exc.code,
        message=exc.message,
        data=None
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.dict()
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
    response = UnifiedResponse.error(
        code=exc.code,
        message=exc.message or "系统处理失败",
        data=None
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.dict()
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
    error_info = str(exc.errors())
    log.warning(f"ValidationError: {error_info}", extra={"path": request.url.path, "method": request.method})
    
    # 提取验证错误信息
    error_details = []
    for error in exc.errors():
        field = "".join([f"[{k}]" if isinstance(k, int) else f".{k}" for k in error["loc"]]).lstrip(".")
        error_details.append(f"{field}: {error['msg']}")
    
    response = UnifiedResponse.error(
        code=10001,  # 参数错误业务代码
        message=". ".join(error_details),
        data=None
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.dict()
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
    error_info = str(exc.errors())
    log.warning(f"PydanticValidationError: {error_info}", extra={"path": request.url.path, "method": request.method})
    
    # 提取验证错误信息
    error_details = []
    for error in exc.errors():
        field = "".join([f"[{k}]" if isinstance(k, int) else f".{k}" for k in error["loc"]]).lstrip(".")
        error_details.append(f"{field}: {error['msg']}")
    
    response = UnifiedResponse.error(
        code=10002,  # 数据验证错误业务代码
        message=". ".join(error_details),
        data=None
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.dict()
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
    response = UnifiedResponse.error(
        code=20001,  # 数据库操作错误业务代码
        message="数据库操作失败",
        data=None
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.dict()
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
    response = UnifiedResponse.error(
        code=20002,  # 系统内部错误业务代码
        message="系统处理失败",
        data=None
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.dict()
    )
