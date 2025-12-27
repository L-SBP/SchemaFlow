"""
向量数据库服务模块。

使用 ChromaDB 作为向量数据库，支持：
- 历史对话的向量存储与检索
- 领域知识的向量存储与检索  
- Schema/DDL 片段的向量存储与检索

ChromaDB 部署模式：
- 内嵌模式 (Embedded): 本地开发，无需额外服务
- HTTP 客户端模式: 连接 Docker 中的 ChromaDB 服务（生产环境）

使用方式：
    from service.vector_db_service import vector_db_service
    
    # 添加文档
    await vector_db_service.add_documents(
        collection_name="knowledge",
        documents=["文档1", "文档2"],
        metadatas=[{"id": 1}, {"id": 2}],
        ids=["doc1", "doc2"]
    )
    
    # 相似度搜索
    results = await vector_db_service.search(
        collection_name="knowledge",
        query_text="查询文本",
        top_k=5
    )
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings

from core.log import log
from core.config import settings


class VectorDBService:
    """
    向量数据库服务类。
    
    封装 ChromaDB 操作，提供异步接口。
    支持多个 Collection（集合）用于不同类型的数据。
    
    部署模式：
    - use_http_client=False: 内嵌模式，数据存储在本地
    - use_http_client=True: HTTP 客户端模式，连接 Docker 中的 ChromaDB
    """
    
    # 预定义的 Collection 名称
    COLLECTION_HISTORY = "chat_history"          # 历史对话
    COLLECTION_KNOWLEDGE = "domain_knowledge"    # 领域知识
    COLLECTION_DDL = "table_ddl"                 # 表 DDL（CREATE TABLE 语句）
    # 保留旧名称作为别名，兼容旧代码
    COLLECTION_SCHEMA = COLLECTION_DDL
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        use_http_client: Optional[bool] = None,
        persist_directory: Optional[str] = None
    ):
        """
        初始化向量数据库服务。
        
        Args:
            host: ChromaDB 服务主机（HTTP 模式）
            port: ChromaDB 服务端口（HTTP 模式）
            use_http_client: 是否使用 HTTP 客户端模式
            persist_directory: 持久化目录路径（内嵌模式）
        """
        # 从配置读取默认值
        chroma_config = getattr(settings, 'chroma', None)
        
        self.host = host or (chroma_config.host if chroma_config else "localhost")
        self.port = port or (chroma_config.port if chroma_config else 8100)
        self.use_http_client = use_http_client if use_http_client is not None else (
            chroma_config.use_http_client if chroma_config else False
        )
        
        # 内嵌模式的持久化目录
        if persist_directory:
            self.persist_directory = persist_directory
        elif chroma_config:
            self.persist_directory = chroma_config.persist_directory
        else:
            self.persist_directory = "data/chroma_db"
        
        # 确保内嵌模式目录存在
        if not self.use_http_client:
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        self._client = None
        self._collections: Dict[str, Any] = {}
        
        log.info(f"VectorDB mode: {'HTTP Client' if self.use_http_client else 'Embedded'}")
        
    def _get_client(self) -> chromadb.ClientAPI:
        """获取或创建 ChromaDB 客户端（懒加载）。"""
        if self._client is None:
            if self.use_http_client:
                # HTTP 客户端模式：连接 Docker 中的 ChromaDB
                self._client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port,
                    settings=Settings(
                        anonymized_telemetry=False
                    )
                )
                log.info(f"ChromaDB HTTP client connected to {self.host}:{self.port}")
            else:
                # 内嵌模式：本地持久化
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                log.info(f"ChromaDB embedded client initialized at {self.persist_directory}")
        return self._client
    
    def _get_collection(self, collection_name: str) -> Any:
        """
        获取或创建 Collection。
        
        Args:
            collection_name: 集合名称
            
        Returns:
            ChromaDB Collection 对象
        """
        if collection_name not in self._collections:
            client = self._get_client()
            self._collections[collection_name] = client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
            )
            log.info(f"Collection '{collection_name}' loaded/created")
        return self._collections[collection_name]
    
    async def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        添加文档到向量数据库。
        
        Args:
            collection_name: 集合名称
            documents: 文档文本列表
            embeddings: 对应的向量列表
            metadatas: 元数据列表（可选）
            ids: 文档 ID 列表（可选，自动生成）
        """
        if not documents:
            return
            
        # 生成默认 ID
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # 默认元数据
        if metadatas is None:
            metadatas = [{} for _ in documents]
        
        collection = self._get_collection(collection_name)
        
        # ChromaDB 操作是同步的，使用线程池执行
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        )
        log.debug(f"Added {len(documents)} documents to '{collection_name}'")
    
    async def upsert_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: List[str] = None
    ) -> None:
        """
        更新或插入文档（根据 ID）。
        
        Args:
            collection_name: 集合名称
            documents: 文档文本列表
            embeddings: 对应的向量列表
            metadatas: 元数据列表
            ids: 文档 ID 列表（必需）
        """
        if not documents or not ids:
            return
        
        if metadatas is None:
            metadatas = [{} for _ in documents]
        
        collection = self._get_collection(collection_name)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: collection.upsert(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        )
        log.debug(f"Upserted {len(documents)} documents in '{collection_name}'")
    
    async def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        相似度搜索。
        
        Args:
            collection_name: 集合名称
            query_embedding: 查询向量
            top_k: 返回结果数量
            where: 过滤条件（如 {"project_id": 123}）
            include: 返回字段（默认 ["documents", "metadatas", "distances"]）
            
        Returns:
            Dict: 搜索结果，包含 documents, metadatas, distances
        """
        if include is None:
            include = ["documents", "metadatas", "distances"]
        
        collection = self._get_collection(collection_name)
        
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=include
            )
        )
        
        # 解包结果（query 返回的是嵌套列表）
        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results.get("documents") else [],
            "metadatas": results["metadatas"][0] if results.get("metadatas") else [],
            "distances": results["distances"][0] if results.get("distances") else []
        }
    
    async def delete_by_ids(
        self,
        collection_name: str,
        ids: List[str]
    ) -> None:
        """
        根据 ID 删除文档。
        
        Args:
            collection_name: 集合名称
            ids: 要删除的文档 ID 列表
        """
        if not ids:
            return
        
        collection = self._get_collection(collection_name)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: collection.delete(ids=ids)
        )
        log.debug(f"Deleted {len(ids)} documents from '{collection_name}'")
    
    async def delete_by_filter(
        self,
        collection_name: str,
        where: Dict[str, Any]
    ) -> None:
        """
        根据过滤条件删除文档。
        
        Args:
            collection_name: 集合名称
            where: 过滤条件
        """
        collection = self._get_collection(collection_name)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: collection.delete(where=where)
        )
        log.debug(f"Deleted documents from '{collection_name}' with filter: {where}")
    
    async def get_collection_count(self, collection_name: str) -> int:
        """获取集合中的文档数量。"""
        collection = self._get_collection(collection_name)
        
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(
            None,
            lambda: collection.count()
        )
        return count
    
    async def clear_collection(self, collection_name: str) -> None:
        """清空集合中的所有文档。"""
        client = self._get_client()
        
        loop = asyncio.get_event_loop()
        # 删除并重新创建集合
        await loop.run_in_executor(
            None,
            lambda: client.delete_collection(collection_name)
        )
        
        # 从缓存中移除
        if collection_name in self._collections:
            del self._collections[collection_name]
        
        log.info(f"Collection '{collection_name}' cleared")


# 全局单例实例
vector_db_service = VectorDBService()


# =========================================================
# 特定用途的辅助函数
# =========================================================

async def add_chat_history(
    session_id: int,
    message_id: int,
    content: str,
    embedding: List[float],
    role: str = "user"
) -> None:
    """
    添加聊天历史到向量数据库。
    
    Args:
        session_id: 会话 ID
        message_id: 消息 ID
        content: 消息内容
        embedding: 消息向量
        role: 角色（user/assistant）
    """
    await vector_db_service.add_documents(
        collection_name=VectorDBService.COLLECTION_HISTORY,
        documents=[content],
        embeddings=[embedding],
        metadatas=[{
            "session_id": session_id,
            "message_id": message_id,
            "role": role
        }],
        ids=[f"msg_{message_id}"]
    )


async def add_domain_knowledge(
    project_id: int,
    knowledge_id: int,
    term: str,
    definition: str,
    embedding: List[float]
) -> None:
    """
    添加领域知识到向量数据库。
    
    Args:
        project_id: 项目 ID
        knowledge_id: 知识 ID
        term: 术语
        definition: 定义
        embedding: 向量（通常是 term + definition 的组合）
    """
    await vector_db_service.upsert_documents(
        collection_name=VectorDBService.COLLECTION_KNOWLEDGE,
        documents=[f"{term}: {definition}"],
        embeddings=[embedding],
        metadatas=[{
            "project_id": project_id,
            "knowledge_id": knowledge_id,
            "term": term
        }],
        ids=[f"knowledge_{knowledge_id}"]
    )


async def add_schema_fragment(
    project_id: int,
    table_name: str,
    ddl_fragment: str,
    embedding: List[float]
) -> None:
    """
    添加 Schema/DDL 片段到向量数据库。
    
    Args:
        project_id: 项目 ID
        table_name: 表名
        ddl_fragment: DDL 片段（CREATE TABLE 语句）
        embedding: 向量
    """
    await vector_db_service.upsert_documents(
        collection_name=VectorDBService.COLLECTION_DDL,
        documents=[ddl_fragment],
        embeddings=[embedding],
        metadatas=[{
            "project_id": project_id,
            "table_name": table_name
        }],
        ids=[f"ddl_{project_id}_{table_name}"]
    )


async def search_similar_history(
    query_embedding: List[float],
    session_id: int,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    搜索相似的历史对话。
    
    Args:
        query_embedding: 查询向量
        session_id: 会话 ID（限定范围）
        top_k: 返回数量
        
    Returns:
        List[Dict]: 相似的历史消息列表
    """
    results = await vector_db_service.search(
        collection_name=VectorDBService.COLLECTION_HISTORY,
        query_embedding=query_embedding,
        top_k=top_k,
        where={"session_id": session_id}
    )
    
    return [
        {
            "id": results["ids"][i],
            "content": results["documents"][i],
            "metadata": results["metadatas"][i],
            "distance": results["distances"][i]
        }
        for i in range(len(results["ids"]))
    ]


async def search_relevant_knowledge(
    query_embedding: List[float],
    project_id: int,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    搜索相关的领域知识。
    
    Args:
        query_embedding: 查询向量
        project_id: 项目 ID
        top_k: 返回数量
        
    Returns:
        List[Dict]: 相关的领域知识列表
    """
    results = await vector_db_service.search(
        collection_name=VectorDBService.COLLECTION_KNOWLEDGE,
        query_embedding=query_embedding,
        top_k=top_k,
        where={"project_id": project_id}
    )
    
    return [
        {
            "id": results["ids"][i],
            "content": results["documents"][i],
            "metadata": results["metadatas"][i],
            "distance": results["distances"][i]
        }
        for i in range(len(results["ids"]))
    ]


async def search_relevant_schema(
    query_embedding: List[float],
    project_id: int,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    搜索相关的 DDL 片段（CREATE TABLE 语句）。
    
    Args:
        query_embedding: 查询向量
        project_id: 项目 ID
        top_k: 返回数量
        
    Returns:
        List[Dict]: 相关的 DDL 片段列表
    """
    results = await vector_db_service.search(
        collection_name=VectorDBService.COLLECTION_DDL,
        query_embedding=query_embedding,
        top_k=top_k,
        where={"project_id": project_id}
    )
    
    return [
        {
            "id": results["ids"][i],
            "content": results["documents"][i],
            "metadata": results["metadatas"][i],
            "distance": results["distances"][i]
        }
        for i in range(len(results["ids"]))
    ]
