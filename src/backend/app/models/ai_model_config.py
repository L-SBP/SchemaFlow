"""
AI 模型配置模型。

本模块定义了用于存储 AI 对话模型配置的 ORM 模型。
管理员可以动态添加、修改、删除模型配置。
"""

# backend/app/models/ai_model_config.py

from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from core.database import Base


class AIModelConfig(Base):
    """
    AI 模型配置表 ORM 模型（精简版）。

    存储 AI 对话模型的核心配置信息。

    Attributes:
        config_id (int): 配置ID，主键。
        model_name (str): 模型显示名称（同时作为唯一标识）。
        api_url (str): API 接口地址。
        model_id (str): 模型在 API 服务中的标识。
        api_key (str): API 密钥。
        model_type (str): 模型类型（local_finetune, general_llm）。
        created_at (datetime): 创建时间。
        updated_at (datetime): 更新时间。
    """
    __tablename__ = 'ai_model_config'

    __table_args__ = (
        Index('idx_ai_model_config_model_name', 'model_name', unique=True),
        {'comment': 'AI 对话模型配置表，存储模型连接信息'}
    )

    config_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='配置ID'
    )
    model_name = Column(
        String(200),
        nullable=False,
        unique=True,
        comment='模型名称（唯一标识）'
    )
    api_url = Column(
        String(500),
        nullable=False,
        comment='API 接口地址'
    )
    model_id = Column(
        String(200),
        nullable=False,
        comment='模型在 API 服务中的标识'
    )
    api_key = Column(
        String(500),
        nullable=False,
        comment='API 密钥'
    )
    model_type = Column(
        String(50),
        nullable=False,
        default='general_llm',
        comment='模型类型：local_finetune, general_llm'
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='创建时间'
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment='更新时间'
    )

    def to_registry_format(self) -> dict:
        """
        转换为 MODEL_REGISTRY 格式，用于兼容现有代码。
        
        Returns:
            dict: 模型配置字典。
        """
        return {
            "name": self.model_name,
            "api_url": self.api_url,
            "model_id": self.model_id,
            "api_key": self.api_key,
            "type": self.model_type
        }
