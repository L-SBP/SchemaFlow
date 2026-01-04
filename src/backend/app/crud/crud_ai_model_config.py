"""
AI 模型配置 CRUD（精简版）。

本模块提供 AI 模型配置的增删改查操作。
"""

# backend/app/crud/crud_ai_model_config.py

from typing import Optional, List, Dict, Any
from sqlalchemy.future import select
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from models.ai_model_config import AIModelConfig
from schema.ai_model_config import AIModelConfigCreate, AIModelConfigUpdate
from core.exceptions import DatabaseOperationFailedException
from core.log import log


class CRUDAIModelConfig:
    """
    AI 模型配置数据操作类。

    提供 AI 模型配置的增删改查功能。
    """

    @staticmethod
    async def create(db: AsyncSession, config_in: AIModelConfigCreate) -> AIModelConfig:
        """
        创建新的 AI 模型配置。
        
        Args:
            db (AsyncSession): 数据库会话。
            config_in (AIModelConfigCreate): 创建请求数据。
        
        Returns:
            AIModelConfig: 创建的配置对象。
        
        Raises:
            DatabaseOperationFailedException: 如果发生数据库错误。
        """
        try:
            db_obj = AIModelConfig(
                model_name=config_in.model_name,
                api_url=config_in.api_url,
                model_id=config_in.model_id,
                api_key=config_in.api_key,
                model_type=config_in.model_type
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            log.info(f"Created AI model config: {config_in.model_name}")
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            log.error(f"Failed to create AI model config: {e}")
            raise DatabaseOperationFailedException("create AI model config") from e

    @staticmethod
    async def get(db: AsyncSession, config_id: int) -> Optional[AIModelConfig]:
        """
        根据配置ID获取 AI 模型配置。
        
        Args:
            db (AsyncSession): 数据库会话。
            config_id (int): 配置ID。
        
        Returns:
            Optional[AIModelConfig]: 配置对象或 None。
        """
        try:
            query = select(AIModelConfig).where(AIModelConfig.config_id == config_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error(f"Failed to get AI model config by id: {e}")
            raise DatabaseOperationFailedException("get AI model config") from e

    @staticmethod
    async def get_by_name(db: AsyncSession, model_name: str) -> Optional[AIModelConfig]:
        """
        根据 model_name 获取 AI 模型配置。
        
        Args:
            db (AsyncSession): 数据库会话。
            model_name (str): 模型名称。
        
        Returns:
            Optional[AIModelConfig]: 配置对象或 None。
        """
        try:
            query = select(AIModelConfig).where(AIModelConfig.model_name == model_name)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error(f"Failed to get AI model config by name: {e}")
            raise DatabaseOperationFailedException("get AI model config by name") from e

    @staticmethod
    async def get_all(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[AIModelConfig]:
        """
        获取所有 AI 模型配置。
        
        Args:
            db (AsyncSession): 数据库会话。
            skip (int): 跳过记录数。
            limit (int): 返回记录数限制。
        
        Returns:
            List[AIModelConfig]: 配置列表。
        """
        try:
            query = select(AIModelConfig).order_by(AIModelConfig.created_at.asc())
            query = query.offset(skip).limit(limit)
            result = await db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            log.error(f"Failed to get AI model configs: {e}")
            raise DatabaseOperationFailedException("get AI model configs") from e

    @staticmethod
    async def get_count(db: AsyncSession) -> int:
        """
        获取配置总数。
        
        Args:
            db (AsyncSession): 数据库会话。
        
        Returns:
            int: 配置总数。
        """
        try:
            from sqlalchemy import func
            query = select(func.count(AIModelConfig.config_id))
            result = await db.execute(query)
            return result.scalar() or 0
        except SQLAlchemyError as e:
            log.error(f"Failed to count AI model configs: {e}")
            raise DatabaseOperationFailedException("count AI model configs") from e

    @staticmethod
    async def update(
        db: AsyncSession, 
        config_id: int, 
        config_in: AIModelConfigUpdate
    ) -> Optional[AIModelConfig]:
        """
        更新 AI 模型配置。
        
        Args:
            db (AsyncSession): 数据库会话。
            config_id (int): 配置ID。
            config_in (AIModelConfigUpdate): 更新数据。
        
        Returns:
            Optional[AIModelConfig]: 更新后的配置对象或 None。
        """
        try:
            db_obj = await CRUDAIModelConfig.get(db, config_id)
            if not db_obj:
                return None
            
            update_data = config_in.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            log.info(f"Updated AI model config: {db_obj.model_name}")
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            log.error(f"Failed to update AI model config: {e}")
            raise DatabaseOperationFailedException("update AI model config") from e

    @staticmethod
    async def delete(db: AsyncSession, config_id: int) -> bool:
        """
        删除 AI 模型配置。
        
        Args:
            db (AsyncSession): 数据库会话。
            config_id (int): 配置ID。
        
        Returns:
            bool: 是否删除成功。
        """
        try:
            db_obj = await CRUDAIModelConfig.get(db, config_id)
            if not db_obj:
                return False
            
            model_name = db_obj.model_name
            await db.delete(db_obj)
            await db.commit()
            log.info(f"Deleted AI model config: {model_name}")
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            log.error(f"Failed to delete AI model config: {e}")
            raise DatabaseOperationFailedException("delete AI model config") from e

    @staticmethod
    async def get_model_registry(db: AsyncSession) -> Dict[str, Dict[str, Any]]:
        """
        获取所有模型配置，返回 MODEL_REGISTRY 格式。
        
        用于兼容现有的 chat_service 代码。
        
        Args:
            db (AsyncSession): 数据库会话。
        
        Returns:
            Dict[str, Dict[str, Any]]: 模型配置字典，key 为 model_name。
        """
        configs = await CRUDAIModelConfig.get_all(db)
        registry = {}
        for config in configs:
            registry[config.model_name] = config.to_registry_format()
        return registry

    @staticmethod
    async def check_name_exists(db: AsyncSession, model_name: str, exclude_id: int = None) -> bool:
        """
        检查 model_name 是否已存在。
        
        Args:
            db (AsyncSession): 数据库会话。
            model_name (str): 模型名称。
            exclude_id (int): 排除的配置ID（用于更新时检查）。
        
        Returns:
            bool: 是否存在。
        """
        try:
            query = select(AIModelConfig).where(AIModelConfig.model_name == model_name)
            if exclude_id:
                query = query.where(AIModelConfig.config_id != exclude_id)
            result = await db.execute(query)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            log.error(f"Failed to check model name existence: {e}")
            raise DatabaseOperationFailedException("check model name existence") from e


# 单例导出
crud_ai_model_config = CRUDAIModelConfig()
