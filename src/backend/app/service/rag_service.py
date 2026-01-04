"""
RAG 检索服务模块。

整合 Embedding 服务和向量数据库服务，提供完整的 RAG 检索能力。

支持三种检索场景：
1. 历史对话检索 - 根据当前问题检索相似的历史对话
2. 领域知识检索 - 根据问题检索相关的业务术语定义
3. DDL 检索 - 根据问题检索相关的表 DDL（CREATE TABLE 语句）

使用方式：
    from service.rag_service import rag_service
    
    # 检索相关上下文
    context = await rag_service.retrieve_context(
        query="查询所有订单金额大于1000的用户",
        project_id=123,
        session_id=456
    )
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from core.log import log
from service.embedding_service import embedding_service
from service.vector_db_service import (
    vector_db_service,
    VectorDBService,
    search_similar_history,
    search_relevant_knowledge,
    search_relevant_schema as search_relevant_ddl,
    add_chat_history,
    add_domain_knowledge,
    add_schema_fragment as add_ddl_fragment
)


@dataclass
class RAGContext:
    """RAG 检索结果上下文。"""
    relevant_history: List[Dict[str, Any]]      # 相关历史对话
    relevant_knowledge: List[Dict[str, Any]]    # 相关领域知识
    relevant_ddl: List[Dict[str, Any]]          # 相关 DDL 片段（CREATE TABLE 语句）
    query_embedding: List[float]                # 查询向量（可复用）


class RAGService:
    """
    RAG 检索服务类。
    
    整合 Embedding 和 VectorDB，提供端到端的检索能力。
    """
    
    # 检索参数配置
    DEFAULT_HISTORY_TOP_K = 5       # 历史对话检索数量
    DEFAULT_KNOWLEDGE_TOP_K = 3     # 领域知识检索数量
    DEFAULT_DDL_TOP_K = 5           # DDL 片段检索数量（初始检索）
    DEFAULT_DDL_MAX_TABLES = 10     # DDL 最终返回最大表数（包含外键关联表）
    
    # 相似度阈值（余弦距离，越小越相似）
    SIMILARITY_THRESHOLD = 0.8      # 过滤掉距离大于此值的结果
    DDL_FK_BOOST_THRESHOLD = 0.9    # 外键关联表的放宽阈值
    
    def __init__(self):
        """初始化 RAG 服务。"""
        self.embedding = embedding_service
        self.vector_db = vector_db_service
    
    # =========================================================
    # 检索相关方法
    # =========================================================
    
    async def retrieve_context(
        self,
        query: str,
        project_id: int,
        session_id: Optional[int] = None,
        history_top_k: int = None,
        knowledge_top_k: int = None,
        ddl_top_k: int = None,
        enable_history: bool = True,
        enable_knowledge: bool = True,
        enable_ddl: bool = False  # DDL 检索默认关闭，大多数场景全量 DDL 更好
    ) -> RAGContext:
        """
        检索与查询相关的上下文。
        
        Args:
            query: 用户查询
            project_id: 项目 ID
            session_id: 会话 ID（用于历史检索）
            history_top_k: 历史对话检索数量
            knowledge_top_k: 领域知识检索数量
            ddl_top_k: DDL 检索数量
            enable_history: 是否启用历史检索
            enable_knowledge: 是否启用知识检索
            enable_ddl: 是否启用 DDL 检索
            
        Returns:
            RAGContext: 检索结果上下文
        """
        # 设置默认值
        history_top_k = history_top_k or self.DEFAULT_HISTORY_TOP_K
        knowledge_top_k = knowledge_top_k or self.DEFAULT_KNOWLEDGE_TOP_K
        ddl_top_k = ddl_top_k or self.DEFAULT_DDL_TOP_K
        
        # 1. 生成查询向量
        query_embedding = await self.embedding.embed_text(query)
        
        # 2. 并行检索各类上下文
        relevant_history = []
        relevant_knowledge = []
        relevant_ddl = []
        
        # 历史对话检索
        if enable_history and session_id:
            try:
                results = await search_similar_history(
                    query_embedding=query_embedding,
                    session_id=session_id,
                    top_k=history_top_k
                )
                relevant_history = self._filter_by_threshold(results)
                log.debug(f"Retrieved {len(relevant_history)} relevant history items")
            except Exception as e:
                log.warning(f"History retrieval failed: {e}")
        
        # 领域知识检索
        if enable_knowledge:
            try:
                results = await search_relevant_knowledge(
                    query_embedding=query_embedding,
                    project_id=project_id,
                    top_k=knowledge_top_k
                )
                relevant_knowledge = self._filter_by_threshold(results)
                log.debug(f"Retrieved {len(relevant_knowledge)} relevant knowledge items")
            except Exception as e:
                log.warning(f"Knowledge retrieval failed: {e}")
        
        # DDL 检索（含外键关联表权重提升）
        if enable_ddl:
            try:
                results = await search_relevant_ddl(
                    query_embedding=query_embedding,
                    project_id=project_id,
                    top_k=ddl_top_k * 2  # 先多检索一些，后续会扩展外键表
                )
                relevant_ddl = self._filter_by_threshold(results)
                initial_tables = [r.get("metadata", {}).get("table_name", "?") for r in relevant_ddl]
                log.info(f"[RAG-DDL-Initial] Found {len(relevant_ddl)} tables before FK expansion: {initial_tables}")
                
                # 外键关联表扩展：确保被引用的表也被包含
                if relevant_ddl:
                    relevant_ddl = await self._expand_foreign_key_tables(
                        relevant_ddl, project_id, self.DEFAULT_DDL_MAX_TABLES
                    )
                    final_tables = [r.get("metadata", {}).get("table_name", "?") for r in relevant_ddl]
                    log.info(f"[RAG-DDL-Final] After FK expansion: {len(relevant_ddl)} tables: {final_tables}")
                
            except Exception as e:
                log.warning(f"DDL retrieval failed: {e}")
        
        return RAGContext(
            relevant_history=relevant_history,
            relevant_knowledge=relevant_knowledge,
            relevant_ddl=relevant_ddl,
            query_embedding=query_embedding
        )
    
    def _filter_by_threshold(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """根据相似度阈值过滤结果。"""
        return [
            r for r in results
            if r.get("distance", 1.0) <= self.SIMILARITY_THRESHOLD
        ]
    
    async def _expand_foreign_key_tables(
        self,
        ddl_results: List[Dict[str, Any]],
        project_id: int,
        max_tables: int
    ) -> List[Dict[str, Any]]:
        """
        扩展外键关联表。
        
        分析已检索的DDL中的外键引用，确保被引用的表也被包含。
        这样可以保证SQL生成时有完整的表关联信息。
        
        Args:
            ddl_results: 已检索的DDL结果
            project_id: 项目ID
            max_tables: 最大表数量
            
        Returns:
            扩展后的DDL结果列表
        """
        if not ddl_results:
            return ddl_results
        
        # 收集已有的表名
        existing_tables = set()
        for r in ddl_results:
            table_name = r.get("metadata", {}).get("table_name") or r.get("table_name")
            if table_name:
                existing_tables.add(table_name.lower())
        
        # 从DDL中提取外键引用的表
        referenced_tables = set()
        for r in ddl_results:
            ddl_content = r.get("content") or r.get("document") or ""
            refs = self._extract_foreign_key_references(ddl_content)
            for ref_table in refs:
                if ref_table.lower() not in existing_tables:
                    referenced_tables.add(ref_table)
        
        # 如果有未包含的外键引用表，尝试检索它们
        if referenced_tables and len(ddl_results) < max_tables:
            remaining_slots = max_tables - len(ddl_results)
            try:
                for ref_table in list(referenced_tables)[:remaining_slots]:
                    # 用表名作为查询检索对应的DDL
                    ref_embedding = await self.embedding.embed_text(f"CREATE TABLE {ref_table}")
                    ref_results = await search_relevant_ddl(
                        query_embedding=ref_embedding,
                        project_id=project_id,
                        top_k=3
                    )
                    
                    # 找到匹配的表
                    for ref_r in ref_results:
                        ref_table_name = ref_r.get("metadata", {}).get("table_name") or ref_r.get("table_name")
                        if ref_table_name and ref_table_name.lower() == ref_table.lower():
                            # 使用放宽的阈值
                            if ref_r.get("distance", 1.0) <= self.DDL_FK_BOOST_THRESHOLD:
                                ddl_results.append(ref_r)
                                existing_tables.add(ref_table.lower())
                                log.debug(f"Added FK referenced table: {ref_table}")
                            break
            except Exception as e:
                log.warning(f"Failed to expand FK tables: {e}")
        
        return ddl_results[:max_tables]
    
    def _extract_foreign_key_references(self, ddl_content: str) -> List[str]:
        """
        从DDL中提取外键引用的表名。
        
        Args:
            ddl_content: DDL内容
            
        Returns:
            被引用的表名列表
        """
        referenced = []
        
        # 匹配 REFERENCES table_name 模式
        # 支持: REFERENCES table(col), REFERENCES `table`(col), REFERENCES "table"(col)
        pattern = r'REFERENCES\s+[`"\[]?(\w+)[`"\]]?\s*\('
        matches = re.findall(pattern, ddl_content, re.IGNORECASE)
        referenced.extend(matches)
        
        # 匹配 FOREIGN KEY ... REFERENCES 模式
        pattern2 = r'FOREIGN\s+KEY\s*\([^)]+\)\s*REFERENCES\s+[`"\[]?(\w+)[`"\]]?'
        matches2 = re.findall(pattern2, ddl_content, re.IGNORECASE)
        referenced.extend(matches2)
        
        return list(set(referenced))
    
    # =========================================================
    # 索引相关方法（写入向量数据库）
    # =========================================================
    
    async def index_message(
        self,
        session_id: int,
        message_id: int,
        content: str,
        role: str = "user"
    ) -> None:
        """
        将消息索引到向量数据库。
        
        Args:
            session_id: 会话 ID
            message_id: 消息 ID
            content: 消息内容
            role: 角色（user/assistant）
        """
        try:
            # 生成向量
            embedding = await self.embedding.embed_text(content)
            
            # 存入向量数据库
            await add_chat_history(
                session_id=session_id,
                message_id=message_id,
                content=content,
                embedding=embedding,
                role=role
            )
            log.debug(f"Indexed message {message_id} for session {session_id}")
        except Exception as e:
            log.error(f"Failed to index message: {e}")
            # 索引失败不应影响主流程，静默失败
    
    async def index_knowledge(
        self,
        project_id: int,
        knowledge_id: int,
        term: str,
        definition: str
    ) -> None:
        """
        将领域知识索引到向量数据库。
        
        Args:
            project_id: 项目 ID
            knowledge_id: 知识 ID
            term: 术语
            definition: 定义
        """
        try:
            # 组合 term 和 definition 生成向量
            combined_text = f"{term}: {definition}"
            embedding = await self.embedding.embed_text(combined_text)
            
            await add_domain_knowledge(
                project_id=project_id,
                knowledge_id=knowledge_id,
                term=term,
                definition=definition,
                embedding=embedding
            )
            log.debug(f"Indexed knowledge {knowledge_id} for project {project_id}")
        except Exception as e:
            log.error(f"Failed to index knowledge: {e}")
    
    async def index_ddl(
        self,
        project_id: int,
        ddl_text: str
    ) -> None:
        """
        将 DDL 分片索引到向量数据库。
        
        DDL 会按表进行分片，每张表的 CREATE TABLE 语句单独索引。
        这样可以精确检索与用户问题相关的表结构。
        
        Args:
            project_id: 项目 ID
            ddl_text: 完整 DDL 文本（包含所有 CREATE TABLE 语句）
        """
        try:
            # 分割 DDL 为表级片段
            table_fragments = self._split_ddl_to_tables(ddl_text)
            
            for table_name, fragment in table_fragments.items():
                embedding = await self.embedding.embed_text(fragment)
                await add_ddl_fragment(
                    project_id=project_id,
                    table_name=table_name,
                    ddl_fragment=fragment,
                    embedding=embedding
                )
            
            log.info(f"Indexed {len(table_fragments)} table DDLs for project {project_id}")
        except Exception as e:
            log.error(f"Failed to index DDL: {e}")
    
    def _split_ddl_to_tables(self, ddl_text: str) -> Dict[str, str]:
        """
        将 DDL 分割为表级片段。
        
        Args:
            ddl_text: 完整 DDL
            
        Returns:
            Dict[str, str]: {table_name: ddl_fragment}
        """
        tables = {}
        
        # 使用正则匹配 CREATE TABLE 语句
        # 支持 MySQL、PostgreSQL、SQLite 语法
        pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\[]?(\w+)[`"\]]?\s*\([^;]+\);?'
        
        matches = re.finditer(pattern, ddl_text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            table_name = match.group(1)
            ddl_fragment = match.group(0).strip()
            tables[table_name] = ddl_fragment
        
        # 如果正则没匹配到，返回整个 DDL 作为一个片段
        if not tables and ddl_text.strip():
            tables["_full_schema"] = ddl_text
        
        return tables
    
    async def index_knowledge_batch(
        self,
        project_id: int,
        knowledge_list: List[Dict[str, Any]]
    ) -> None:
        """
        批量索引领域知识。
        
        Args:
            project_id: 项目 ID
            knowledge_list: 知识列表 [{"knowledge_id": int, "term": str, "definition": str}]
        """
        if not knowledge_list:
            return
        
        try:
            # 批量生成向量
            texts = [f"{k['term']}: {k['definition']}" for k in knowledge_list]
            embeddings = await self.embedding.embed_texts(texts)
            
            # 准备数据
            documents = texts
            ids = [f"knowledge_{k['knowledge_id']}" for k in knowledge_list]
            metadatas = [
                {
                    "project_id": project_id,
                    "knowledge_id": k['knowledge_id'],
                    "term": k['term']
                }
                for k in knowledge_list
            ]
            
            # 批量写入
            await self.vector_db.upsert_documents(
                collection_name=VectorDBService.COLLECTION_KNOWLEDGE,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            log.info(f"Batch indexed {len(knowledge_list)} knowledge items for project {project_id}")
        except Exception as e:
            log.error(f"Failed to batch index knowledge: {e}")
    
    # =========================================================
    # 删除相关方法
    # =========================================================
    
    async def delete_session_history(self, session_id: int) -> None:
        """删除会话的所有历史向量。"""
        await self.vector_db.delete_by_filter(
            collection_name=VectorDBService.COLLECTION_HISTORY,
            where={"session_id": session_id}
        )
        log.info(f"Deleted history vectors for session {session_id}")
    
    async def delete_project_knowledge(self, project_id: int) -> None:
        """删除项目的所有领域知识向量。"""
        await self.vector_db.delete_by_filter(
            collection_name=VectorDBService.COLLECTION_KNOWLEDGE,
            where={"project_id": project_id}
        )
        log.info(f"Deleted knowledge vectors for project {project_id}")
    
    async def delete_project_ddl(self, project_id: int) -> None:
        """删除项目的所有 DDL 向量。"""
        await self.vector_db.delete_by_filter(
            collection_name=VectorDBService.COLLECTION_SCHEMA,
            where={"project_id": project_id}
        )
        log.info(f"Deleted DDL vectors for project {project_id}")
    
    async def delete_knowledge_item(self, knowledge_id: int) -> None:
        """删除单条领域知识的向量。"""
        await self.vector_db.delete_by_ids(
            collection_name=VectorDBService.COLLECTION_KNOWLEDGE,
            ids=[f"knowledge_{knowledge_id}"]
        )


# 全局单例实例
rag_service = RAGService()


# =========================================================
# 便捷函数（供其他模块直接调用）
# =========================================================

async def retrieve_chat_context(
    query: str,
    project_id: int,
    session_id: int,
    history_top_k: int = 5,
    knowledge_top_k: int = 5,
    enable_ddl: bool = True,
    ddl_top_k: int = 5
) -> RAGContext:
    """
    检索聊天所需的上下文（便捷函数）。
    
    专门为 chat_service 设计，默认启用历史、知识和DDL检索。
    DDL检索会自动扩展外键关联表。
    
    Args:
        query: 用户问题
        project_id: 项目 ID
        session_id: 会话 ID
        history_top_k: 历史检索数量
        knowledge_top_k: 知识检索数量
        enable_ddl: 是否启用DDL检索
        ddl_top_k: DDL检索数量
        
    Returns:
        RAGContext: 检索结果
    """
    return await rag_service.retrieve_context(
        query=query,
        project_id=project_id,
        session_id=session_id,
        history_top_k=history_top_k,
        knowledge_top_k=knowledge_top_k,
        ddl_top_k=ddl_top_k,
        enable_history=True,
        enable_knowledge=True,
        enable_ddl=enable_ddl
    )


async def index_new_message(
    session_id: int,
    message_id: int,
    content: str,
    role: str = "user"
) -> None:
    """
    索引新消息（便捷函数）。
    
    Args:
        session_id: 会话 ID
        message_id: 消息 ID
        content: 消息内容
        role: 角色
    """
    await rag_service.index_message(
        session_id=session_id,
        message_id=message_id,
        content=content,
        role=role
    )
