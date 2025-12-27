"""
Embedding 服务模块。

负责调用阿里云百炼的 text-embedding-v4 模型生成文本向量。
支持单文本和批量文本的向量化。

使用方式：
    from service.embedding_service import embedding_service
    
    # 单文本向量化
    vector = await embedding_service.embed_text("你的文本")
    
    # 批量向量化
    vectors = await embedding_service.embed_texts(["文本1", "文本2"])
"""

import asyncio
from typing import List, Optional
from openai import AsyncOpenAI
from core.log import log
from core.config import settings


class EmbeddingService:
    """
    Embedding 服务类。
    
    使用阿里云百炼的 text-embedding-v4 模型。
    支持自定义向量维度（默认1024）。
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None
    ):
        """
        初始化 Embedding 服务。
        
        Args:
            api_key: 阿里云百炼 API Key
            base_url: API 基础 URL
            model: 模型名称
            dimensions: 向量维度（text-embedding-v4 支持 256-2048）
        """
        # 从配置读取（必须配置）
        embedding_config = getattr(settings, 'embedding', None)
        if not embedding_config:
            raise ValueError("Embedding 配置未找到，请检查 config.yaml 中的 embedding 配置")
        
        self.api_key = api_key or embedding_config.api_key
        self.base_url = base_url or embedding_config.base_url
        self.model = model or embedding_config.model
        self.dimensions = dimensions or embedding_config.dimensions
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
    async def embed_text(self, text: str) -> List[float]:
        """
        将单个文本转换为向量。
        
        Args:
            text: 输入文本
            
        Returns:
            List[float]: 文本的向量表示
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            log.error(f"Embedding generation failed: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转换为向量。
        
        Args:
            texts: 输入文本列表
            
        Returns:
            List[List[float]]: 向量列表，顺序与输入文本对应
        """
        if not texts:
            return []
        
        try:
            # 阿里云百炼支持批量请求，最多一次处理25条
            batch_size = 25
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    dimensions=self.dimensions,
                    encoding_format="float"
                )
                # 按索引排序，确保顺序正确
                batch_embeddings = sorted(response.data, key=lambda x: x.index)
                all_embeddings.extend([item.embedding for item in batch_embeddings])
            
            return all_embeddings
        except Exception as e:
            log.error(f"Batch embedding generation failed: {e}")
            raise
    
    async def embed_with_cache_key(self, text: str, prefix: str = "") -> tuple:
        """
        生成文本向量并返回缓存键。
        
        Args:
            text: 输入文本
            prefix: 缓存键前缀
            
        Returns:
            tuple: (cache_key, embedding)
        """
        import hashlib
        
        # 生成文本的哈希作为缓存键
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:16]
        cache_key = f"{prefix}:{text_hash}" if prefix else text_hash
        
        embedding = await self.embed_text(text)
        return cache_key, embedding


# 全局单例实例
embedding_service = EmbeddingService()


# =========================================================
# 便捷函数
# =========================================================

async def get_embedding(text: str) -> List[float]:
    """
    便捷函数：获取单个文本的向量。
    
    Args:
        text: 输入文本
        
    Returns:
        List[float]: 向量
    """
    return await embedding_service.embed_text(text)


async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    便捷函数：批量获取文本向量。
    
    Args:
        texts: 文本列表
        
    Returns:
        List[List[float]]: 向量列表
    """
    return await embedding_service.embed_texts(texts)
