"""
AI 模型配置 Schema（精简版）。

本模块定义了 AI 模型配置管理所需的 Pydantic 模型。
包含创建、更新、查询等操作的请求和响应结构。
"""

# backend/app/schema/ai_model_config.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ----------------------------------------------------------------------
# 创建请求
# ----------------------------------------------------------------------

class AIModelConfigCreate(BaseModel):
    """
    创建 AI 模型配置请求 Schema。

    Attributes:
        model_name (str): 模型名称（唯一标识）。
        api_url (str): API 接口地址。
        model_id (str): 模型在 API 服务中的标识。
        api_key (str): API 密钥（非 preset 模型填写；preset 模型留空走 api_key_env 引用）。
        api_key_env (str): 环境变量名（preset 模型通过 env 引用密钥）。
        model_type (str): 模型类型。
    """
    model_name: str = Field(..., min_length=1, max_length=200, description="模型名称")
    api_url: str = Field(..., min_length=1, max_length=500, description="API 接口地址")
    model_id: str = Field(..., min_length=1, max_length=200, description="模型在 API 服务中的标识")
    api_key: str = Field(default="", max_length=500, description="API 密钥")
    api_key_env: str = Field(default="", max_length=64, description="环境变量名，引用 .env 中的密钥")
    model_type: str = Field(default="general_llm", description="模型类型：local_finetune, general_llm")
    provider: str = Field(default="openai_compatible", description="模型供应商")

    # 禁用 Pydantic 保护命名空间，允许 model_ 前缀字段
    model_config = ConfigDict(protected_namespaces=())


# ----------------------------------------------------------------------
# 更新请求
# ----------------------------------------------------------------------

class AIModelConfigUpdate(BaseModel):
    """
    更新 AI 模型配置请求 Schema。
    
    所有字段均为可选，仅更新提供的字段。
    """
    model_name: Optional[str] = Field(None, min_length=1, max_length=200, description="模型名称")
    api_url: Optional[str] = Field(None, min_length=1, max_length=500, description="API 接口地址")
    model_id: Optional[str] = Field(None, min_length=1, max_length=200, description="模型在 API 服务中的标识")
    api_key: Optional[str] = Field(None, max_length=500, description="API 密钥")
    api_key_env: Optional[str] = Field(None, max_length=64, description="环境变量名")
    model_type: Optional[str] = Field(None, description="模型类型")
    provider: Optional[str] = Field(None, description="模型供应商")

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# ----------------------------------------------------------------------
# 响应模型
# ----------------------------------------------------------------------

class AIModelConfigResponse(BaseModel):
    """
    AI 模型配置响应 Schema（不含敏感信息）。

    Attributes:
        config_id (int): 配置ID。
        model_name (str): 模型名称。
        api_url (str): API 接口地址。
        model_id (str): 模型在 API 服务中的标识。
        provider (str): 适配器类型。
        model_type (str): 模型类型。
        created_at (datetime): 创建时间。
        updated_at (datetime): 更新时间。
    """
    config_id: int
    model_name: str
    api_url: str
    model_id: str
    provider: str = "openai_compatible"
    model_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class AIModelConfigDetailResponse(AIModelConfigResponse):
    """
    AI 模型配置详细响应 Schema（包含脱敏的 API Key）。
    
    用于管理员查看详情时，显示部分隐藏的 API Key。
    """
    api_key_masked: str = Field(..., description="脱敏后的 API 密钥")

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class AIModelConfigListResponse(BaseModel):
    """
    AI 模型配置列表响应 Schema。

    Attributes:
        total (int): 总数。
        items (List[AIModelConfigResponse]): 配置列表。
    """
    total: int
    items: List[AIModelConfigResponse]

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# 测试连接请求/响应
# ----------------------------------------------------------------------

class AIModelTestConnectionRequest(BaseModel):
    """
    测试 AI 模型连接请求 Schema。
    
    支持两种模式：
    1. 新建模式：传递 api_key
    2. 编辑模式：传递 config_id，使用已保存的密钥
    """
    api_url: str = Field(..., min_length=1, max_length=500, description="API 接口地址")
    api_key: Optional[str] = Field(None, max_length=500, description="API 密钥（新建模式必填）")
    model_id: str = Field(..., min_length=1, max_length=200, description="模型 ID")
    config_id: Optional[int] = Field(None, description="配置 ID（编辑模式下使用已保存的密钥）")

    model_config = ConfigDict(protected_namespaces=())


class AIModelTestConnectionResponse(BaseModel):
    """
    测试 AI 模型连接响应 Schema。
    """
    success: bool = Field(..., description="连接是否成功")
    message: str = Field(..., description="连接结果描述")
    response_time_ms: Optional[int] = Field(None, description="响应时间（毫秒）")

    model_config = ConfigDict(protected_namespaces=())


# ----------------------------------------------------------------------
# 前端下拉选项响应
# ----------------------------------------------------------------------

class AIModelOption(BaseModel):
    """
    AI 模型选项（供前端下拉框使用）。

    Attributes:
        model_name (str): 模型名称（作为 value 和 label）。
        model_type (str): 模型类型。
    """
    model_name: str
    model_type: str

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class AIModelOptionsResponse(BaseModel):
    """
    AI 模型选项列表响应。
    """
    items: List[AIModelOption]

    model_config = ConfigDict(from_attributes=True)
