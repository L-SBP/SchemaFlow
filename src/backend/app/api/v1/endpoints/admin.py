"""
管理员 API 端点。提供用户管理、公告管理、违规记录查看及系统统计看板等管理员专属功能。
"""
from typing import Optional, List, Literal, Any
from fastapi import APIRouter, Depends, Query, Path, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession as Session

# 导入 Service 和 Schema
from service import admin_service as service
from schema.admin import (
    AdminUserListResponse, AdminUpdateUserStatusRequest, AdminUpdateUserStatusResponse,
    AdminUpdateUserQuotaRequest, AdminUpdateUserQuotaResponse,
    AnnouncementCreateRequest, AnnouncementUpdateRequest, AnnouncementResponse,
    AdminListResponse, AdminListItem, ViolationLogListResponse, AdminStatsResponse,
    AdminUserDetailResponse
)
from schema.user import UserMe
from schema.unified_response import UnifiedResponse, PageData
# 导入依赖
from api.v1.deps import get_db, get_current_admin_user
from core.exceptions import ItemNotFoundException
from core.exceptions import ValidationException

router = APIRouter()

# 统一管理员权限依赖
AdminDependency = Depends(get_current_admin_user)

# 统一分页参数 DTO
class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    ):
        self.page = page
        self.page_size = page_size

# ----------------------------------------------------------------------
# 4.1. 用户管理
# ----------------------------------------------------------------------
@router.get("/users", response_model=UnifiedResponse[PageData[List[AdminUserDetailResponse]]], summary="4.1.1 获取用户列表")
async def get_user_list(
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="按用户名/邮箱搜索"),
    # 变量名改为 filter_status，增加 alias="status"
    filter_status: Literal["normal", "suspended", "banned", "all"] = Query("all", alias="status", description="按状态筛选"),
) -> Any:
    """
    获取用户列表，支持搜索和筛选。

    Args:
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。
        pagination (PaginationParams): 分页参数。
        search (Optional[str]): 按用户名/邮箱搜索关键字。
        filter_status (Literal["normal", "suspended", "banned", "all"]): 按状态筛选用户。

    Returns:
        UnifiedResponse[PageData[List[AdminUserDetailResponse]]]: 用户列表响应。
    """
    # 这里传入 filter_status
    result = await service.get_admin_user_list_service(
        db, pagination.page, pagination.page_size, search, filter_status
    )
    page_data = PageData(
        total=result.total, page=result.page, page_size=result.page_size, items=result.items
    )
    return UnifiedResponse.success(data=page_data, message="获取用户列表成功")


@router.patch("/users/{user_id}/status", response_model=UnifiedResponse[AdminUpdateUserStatusResponse], summary="4.1.2 修改用户状态 (封禁/解封)")
async def update_user_status(
    # 修正：将 data 移到 user_id 之前
    data: AdminUpdateUserStatusRequest,
    user_id: int = Path(..., description="目标用户ID"),
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    封禁或解封用户。

    Args:
        data (AdminUpdateUserStatusRequest): 用户状态更新请求体。
        user_id (int): 目标用户ID。
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        UnifiedResponse[AdminUpdateUserStatusResponse]: 更新后的用户状态信息。
    """
    result = await service.update_user_status_service(db, user_id, data, admin_user.user_id)
    return UnifiedResponse.success(data=result, message="修改用户状态成功")


@router.patch("/users/{user_id}/quota", response_model=UnifiedResponse[AdminUpdateUserQuotaResponse], summary="4.1.3 调整用户资源额度")
async def update_user_quota(
    # 修正：将 data 移到 user_id 之前
    request: Request,  # 添加 Request 依赖
    data: AdminUpdateUserQuotaRequest,
    user_id: int = Path(..., description="目标用户ID"),
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    调整用户的最大数据库额度。

    Args:
        request: HTTP请求对象，用于检查原始请求体。
        data (AdminUpdateUserQuotaRequest): 用户额度更新请求体。
        user_id (int): 目标用户ID。
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        UnifiedResponse[AdminUpdateUserQuotaResponse]: 更新后的用户额度信息。
    """
    # 额外验证：检查原始请求体是否包含科学计数法或小数
    import json
    
    # 获取原始请求体以进行额外验证
    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        body_json = json.loads(body_str)
        
        max_databases_raw = body_json.get('max_databases')
        
        # 检查是否为科学计数法格式（字符串形式）
        if isinstance(max_databases_raw, str) and ('e' in max_databases_raw.lower() or 'E' in max_databases_raw):
            raise ValidationException("不支持科学计数法格式")
        
        # 检查是否为小数（字符串形式包含小数点）
        if isinstance(max_databases_raw, str) and '.' in max_databases_raw:
            raise ValidationException("额度必须为整数")
        
        # 检查是否为小数（数值形式且不是整数）
        if isinstance(max_databases_raw, float) and not max_databases_raw.is_integer():
            raise ValidationException("额度必须为整数")
            
    except (json.JSONDecodeError, AttributeError):
        # 如果无法获取原始请求体，则跳过额外验证
        pass

    result = await service.update_user_quota_service(db, user_id, data)
    return UnifiedResponse.success(data=result, message="调整用户资源额度成功")


@router.get("/users/{user_id}", response_model=UnifiedResponse[AdminUserDetailResponse], summary="4.1.4 获取用户详情")
async def get_user_detail(
    user_id: int = Path(..., description="目标用户ID"),
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
    project_limit: int = Query(100, ge=0, le=500, description="返回的项目条目数量上限"),
    login_limit: int = Query(20, ge=0, le=200, description="返回的登录历史条目数量上限"),
) -> Any:
    """管理员查看用户详情：额度、项目列表、登录历史。"""
    result = await service.get_admin_user_detail_service(
        db, user_id=user_id, project_limit=project_limit, login_limit=login_limit
    )
    return UnifiedResponse.success(data=result, message="获取用户详情成功")

# ----------------------------------------------------------------------
# 4.2. 公告管理
# ----------------------------------------------------------------------

@router.post("/announcements", response_model=UnifiedResponse[AnnouncementResponse], summary="4.2.1 创建公告")
async def create_announcement(
    data: AnnouncementCreateRequest,
    db: Session = Depends(get_db),
    current_admin: UserMe = AdminDependency,
) -> Any:
    """
    创建新的系统公告。

    Args:
        data (AnnouncementCreateRequest): 公告创建请求体。
        db (Session): 数据库会话。
        current_admin (UserMe): 当前管理员用户。

    Returns:
        UnifiedResponse[AnnouncementResponse]: 创建后的公告信息。
    """
    result = await service.create_announcement_service(db, data, current_admin.user_id)
    return UnifiedResponse.success(data=result, message="创建公告成功")


@router.put("/announcements/{announcement_id}", response_model=UnifiedResponse[AnnouncementResponse], summary="4.2.2 更新公告")
async def update_announcement(
    # 修正：将 data 移到 announcement_id 之前
    data: AnnouncementUpdateRequest,
    announcement_id: int = Path(..., description="公告ID"),
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    更新公告内容和状态。

    Args:
        data (AnnouncementUpdateRequest): 公告更新请求体。
        announcement_id (int): 公告ID。
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        UnifiedResponse[AnnouncementResponse]: 更新后的公告信息。
    """
    result = await service.update_announcement_service(db, announcement_id, data)
    return UnifiedResponse.success(data=result, message="更新公告成功")


@router.delete("/announcements/{announcement_id}", response_model=UnifiedResponse[None], summary="4.2.3 删除公告")
async def delete_announcement(
    announcement_id: int = Path(..., description="公告ID"),
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    删除指定的公告。

    Args:
        announcement_id (int): 公告ID。
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        UnifiedResponse[None]: 删除结果响应。
    """
    await service.delete_announcement_service(db, announcement_id)
    return UnifiedResponse.success(message="删除公告成功")

# ----------------------------------------------------------------------
# 4.3. 管理员状态 / 4.4. 违规记录与统计
# ----------------------------------------------------------------------

@router.get("/admins", response_model=UnifiedResponse[PageData[List[AdminListItem]]], summary="4.3.1 获取管理员列表")
async def get_admin_list(
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
    pagination: PaginationParams = Depends(),
) -> Any:
    """
    获取所有管理员的列表。

    Args:
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。
        pagination (PaginationParams): 分页参数。

    Returns:
        UnifiedResponse[PageData[List[AdminListItem]]]: 管理员列表响应。
    """
    result = await service.get_admin_list_service(db, pagination.page, pagination.page_size)
    page_data = PageData(
        total=result.total, page=result.page, page_size=result.page_size, items=result.items
    )
    return UnifiedResponse.success(data=page_data, message="获取管理员列表成功")


@router.get("/violations", response_model=UnifiedResponse[PageData[List[Any]]], summary="4.4.2 获取违规记录列表")
async def get_violation_logs(
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
    pagination: PaginationParams = Depends(),
    risk_level: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = Query(None, description="风险等级筛选"),
    resolution_status: Optional[Literal["pending", "in_progress", "resolved", "ignored"]] = Query(None, description="处理状态筛选"),
) -> Any:
    """
    获取用户违规操作记录列表，支持筛选。

    Args:
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。
        pagination (PaginationParams): 分页参数。
        risk_level (Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]]): 风险等级筛选。
        resolution_status (Optional[Literal["pending", "in_progress", "resolved", "ignored"]]): 处理状态筛选。

    Returns:
        UnifiedResponse[PageData[List[Any]]]: 违规记录列表响应。
    """
    result = await service.get_violation_logs_service(
        db, pagination.page, pagination.page_size, risk_level, resolution_status
    )
    page_data = PageData(
        total=result.total, page=result.page, page_size=result.page_size, items=result.items
    )
    return UnifiedResponse.success(data=page_data, message="获取违规记录列表成功")


@router.get("/dashboard/stats", response_model=UnifiedResponse[AdminStatsResponse], summary="4.4.1 获取系统统计看板")
async def get_system_stats(
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    获取系统运行的实时统计数据。

    Args:
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        UnifiedResponse[AdminStatsResponse]: 系统统计响应。
    """
    result = await service.get_admin_stats_service(db)
    return UnifiedResponse.success(data=result, message="获取系统统计数据成功")


# ----------------------------------------------------------------------
# 4.5. AI 模型配置管理
# ----------------------------------------------------------------------

from schema.ai_model_config import (
    AIModelConfigCreate, AIModelConfigUpdate, AIModelConfigResponse,
    AIModelConfigDetailResponse, AIModelConfigListResponse, AIModelOptionsResponse,
    AIModelTestConnectionRequest, AIModelTestConnectionResponse
)
from crud.crud_ai_model_config import crud_ai_model_config
import httpx
import time


@router.get("/ai-models", response_model=UnifiedResponse[AIModelConfigListResponse], summary="4.5.1 获取 AI 模型配置列表")
async def get_ai_model_configs(
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
) -> Any:
    """
    获取 AI 模型配置列表。

    Args:
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。
        page (int): 页码。
        page_size (int): 每页大小。

    Returns:
        UnifiedResponse[AIModelConfigListResponse]: 模型配置列表响应。
    """
    skip = (page - 1) * page_size
    configs = await crud_ai_model_config.get_all(db, skip=skip, limit=page_size)
    total = await crud_ai_model_config.get_count(db)
    
    items = [AIModelConfigResponse.model_validate(config) for config in configs]
    result = AIModelConfigListResponse(total=total, items=items)
    return UnifiedResponse.success(data=result, message="获取 AI 模型配置列表成功")


@router.get("/ai-models/{config_id}", response_model=UnifiedResponse[AIModelConfigDetailResponse], summary="4.5.2 获取 AI 模型配置详情")
async def get_ai_model_config(
    config_id: int = Path(..., description="配置ID"),
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    获取指定 AI 模型配置的详细信息。

    Args:
        config_id (int): 配置ID。
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        UnifiedResponse[AIModelConfigDetailResponse]: 模型配置详情响应。
    """
    config = await crud_ai_model_config.get(db, config_id)
    if not config:
        raise ItemNotFoundException("AI 模型配置")
    
    # 脱敏 API Key：只显示前4位和后4位
    api_key = config.api_key
    if len(api_key) > 8:
        api_key_masked = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    else:
        api_key_masked = "*" * len(api_key)
    
    result = AIModelConfigDetailResponse(
        config_id=config.config_id,
        model_name=config.model_name,
        api_url=config.api_url,
        model_id=config.model_id,
        model_type=config.model_type,
        created_at=config.created_at,
        updated_at=config.updated_at,
        api_key_masked=api_key_masked
    )
    return UnifiedResponse.success(data=result, message="获取 AI 模型配置详情成功")


@router.post("/ai-models", response_model=UnifiedResponse[AIModelConfigResponse], summary="4.5.3 创建 AI 模型配置")
async def create_ai_model_config(
    data: AIModelConfigCreate,
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    创建新的 AI 模型配置。

    Args:
        data (AIModelConfigCreate): 创建请求数据。
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        UnifiedResponse[AIModelConfigResponse]: 创建的模型配置响应。
    """
    # 检查 model_name 是否已存在
    if await crud_ai_model_config.check_name_exists(db, data.model_name):
        raise ValidationException(f"模型名称 '{data.model_name}' 已存在")
    
    config = await crud_ai_model_config.create(db, data)
    result = AIModelConfigResponse.model_validate(config)
    return UnifiedResponse.success(data=result, message="创建 AI 模型配置成功")


@router.put("/ai-models/{config_id}", response_model=UnifiedResponse[AIModelConfigResponse], summary="4.5.4 更新 AI 模型配置")
async def update_ai_model_config(
    data: AIModelConfigUpdate,
    config_id: int = Path(..., description="配置ID"),
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    更新指定的 AI 模型配置。

    Args:
        data (AIModelConfigUpdate): 更新请求数据。
        config_id (int): 配置ID。
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        UnifiedResponse[AIModelConfigResponse]: 更新后的模型配置响应。
    """
    # 检查配置是否存在
    existing = await crud_ai_model_config.get(db, config_id)
    if not existing:
        raise ItemNotFoundException("AI 模型配置")
    
    # 如果要更新 model_name，检查新名称是否与其他配置冲突
    if data.model_name and data.model_name != existing.model_name:
        if await crud_ai_model_config.check_name_exists(db, data.model_name, exclude_id=config_id):
            raise ValidationException(f"模型名称 '{data.model_name}' 已存在")
    
    config = await crud_ai_model_config.update(db, config_id, data)
    result = AIModelConfigResponse.model_validate(config)
    return UnifiedResponse.success(data=result, message="更新 AI 模型配置成功")


@router.delete("/ai-models/{config_id}", response_model=UnifiedResponse[None], summary="4.5.5 删除 AI 模型配置")
async def delete_ai_model_config(
    config_id: int = Path(..., description="配置ID"),
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    删除指定的 AI 模型配置。

    Args:
        config_id (int): 配置ID。
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        UnifiedResponse[None]: 删除成功响应。
    """
    # 检查配置是否存在
    existing = await crud_ai_model_config.get(db, config_id)
    if not existing:
        raise ItemNotFoundException("AI 模型配置")
    
    await crud_ai_model_config.delete(db, config_id)
    return UnifiedResponse.success(message="删除 AI 模型配置成功")


@router.post("/ai-models/test-connection", response_model=UnifiedResponse[AIModelTestConnectionResponse], summary="4.5.6 测试 AI 模型连接")
async def test_ai_model_connection(
    data: AIModelTestConnectionRequest,
    db: Session = Depends(get_db),
    admin_user: UserMe = AdminDependency,
) -> Any:
    """
    测试 AI 模型 API 连接是否可用。

    Args:
        data (AIModelTestConnectionRequest): 测试连接请求数据。
        db (Session): 数据库会话。
        admin_user (UserMe): 当前管理员用户。

    Returns:
        UnifiedResponse[AIModelTestConnectionResponse]: 测试结果响应。
    """
    start_time = time.time()
    
    # 清理 URL 中的不可见字符（零宽空格、换行符等）
    import re
    clean_url = re.sub(r'[\x00-\x1f\x7f-\x9f\u200b-\u200d\ufeff]', '', data.api_url.strip())
    clean_model_id = data.model_id.strip()
    
    # 获取 API 密钥：优先使用传入的密钥，否则从数据库获取
    clean_api_key = None
    if data.api_key and data.api_key.strip():
        clean_api_key = data.api_key.strip()
    elif data.config_id:
        # 从数据库获取已保存的密钥
        from crud.crud_ai_model_config import crud_ai_model_config
        existing_config = await crud_ai_model_config.get(db, data.config_id)
        if existing_config:
            clean_api_key = existing_config.api_key
        else:
            return UnifiedResponse.success(AIModelTestConnectionResponse(
                success=False,
                message="配置不存在，无法获取已保存的密钥",
                response_time_ms=0
            ))
    
    if not clean_api_key:
        return UnifiedResponse.success(AIModelTestConnectionResponse(
            success=False,
            message="请提供 API 密钥",
            response_time_ms=0
        ))
    
    try:
        # 构造简单的测试请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 发送简单的对话请求测试连接
            test_payload = {
                "model": clean_model_id,
                "messages": [
                    {"role": "user", "content": "Hi"}
                ],
                "max_tokens": 5,
                "stream": False
            }
            
            headers = {
                "Authorization": f"Bearer {clean_api_key}",
                "Content-Type": "application/json"
            }
            
            response = await client.post(
                clean_url,
                json=test_payload,
                headers=headers
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = AIModelTestConnectionResponse(
                    success=True,
                    message="连接成功，API 可正常使用",
                    response_time_ms=response_time_ms
                )
            elif response.status_code == 401:
                result = AIModelTestConnectionResponse(
                    success=False,
                    message="API 密钥无效或已过期",
                    response_time_ms=response_time_ms
                )
            elif response.status_code == 404:
                result = AIModelTestConnectionResponse(
                    success=False,
                    message=f"模型 ID '{data.model_id}' 不存在",
                    response_time_ms=response_time_ms
                )
            elif response.status_code == 429:
                result = AIModelTestConnectionResponse(
                    success=False,
                    message="请求频率超限，请稍后再试",
                    response_time_ms=response_time_ms
                )
            else:
                try:
                    resp_json = response.json()
                    # 尝试多种错误格式
                    error_detail = (
                        resp_json.get("error", {}).get("message", "") or
                        resp_json.get("message", "") or
                        resp_json.get("detail", "") or
                        resp_json.get("msg", "") or
                        str(resp_json)[:200]
                    )
                except:
                    error_detail = response.text[:200] if response.text else "未知错误"
                result = AIModelTestConnectionResponse(
                    success=False,
                    message=f"请求失败 (HTTP {response.status_code}): {error_detail}",
                    response_time_ms=response_time_ms
                )
                
    except httpx.TimeoutException:
        response_time_ms = int((time.time() - start_time) * 1000)
        result = AIModelTestConnectionResponse(
            success=False,
            message="连接超时，请检查 API 地址是否正确",
            response_time_ms=response_time_ms
        )
    except httpx.ConnectError:
        response_time_ms = int((time.time() - start_time) * 1000)
        result = AIModelTestConnectionResponse(
            success=False,
            message="无法连接到服务器，请检查 API 地址",
            response_time_ms=response_time_ms
        )
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        result = AIModelTestConnectionResponse(
            success=False,
            message=f"测试失败: {str(e)}",
            response_time_ms=response_time_ms
        )
    
    return UnifiedResponse.success(data=result, message="测试完成")
