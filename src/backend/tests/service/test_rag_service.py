"""
RAG 服务测试示例。

演示如何使用 Embedding 和 RAG 服务。

运行方式：
    cd src/backend
    python -m tests.service.test_rag_service
"""

import asyncio
import sys
import os

# 添加 app 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from service.embedding_service import embedding_service, get_embedding, get_embeddings
from service.vector_db_service import vector_db_service, VectorDBService
from service.rag_service import rag_service, retrieve_chat_context


async def test_embedding():
    """测试 Embedding 服务"""
    print("=" * 50)
    print("测试 Embedding 服务")
    print("=" * 50)
    
    # 单文本向量化
    text = "查询所有订单金额大于1000的用户"
    embedding = await get_embedding(text)
    print(f"文本: {text}")
    print(f"向量维度: {len(embedding)}")
    print(f"向量前5个值: {embedding[:5]}")
    print()
    
    # 批量向量化
    texts = [
        "查询用户信息",
        "统计订单数量",
        "获取商品列表"
    ]
    embeddings = await get_embeddings(texts)
    print(f"批量文本数量: {len(texts)}")
    print(f"生成向量数量: {len(embeddings)}")
    print()


async def test_vector_db():
    """测试向量数据库服务"""
    print("=" * 50)
    print("测试向量数据库服务")
    print("=" * 50)
    
    # 添加测试文档
    test_docs = [
        "VIP会员: 消费金额超过10000元的用户",
        "活跃用户: 最近30天有登录的用户",
        "新用户: 注册时间在7天内的用户"
    ]
    
    # 生成向量
    embeddings = await get_embeddings(test_docs)
    
    # 存入向量数据库
    await vector_db_service.add_documents(
        collection_name="test_knowledge",
        documents=test_docs,
        embeddings=embeddings,
        metadatas=[
            {"project_id": 1, "type": "definition"},
            {"project_id": 1, "type": "definition"},
            {"project_id": 1, "type": "definition"}
        ],
        ids=["k1", "k2", "k3"]
    )
    print(f"添加了 {len(test_docs)} 条测试文档")
    
    # 搜索相似文档
    query = "查询消费金额高的用户"
    query_embedding = await get_embedding(query)
    
    results = await vector_db_service.search(
        collection_name="test_knowledge",
        query_embedding=query_embedding,
        top_k=2,
        where={"project_id": 1}
    )
    
    print(f"\n查询: {query}")
    print("搜索结果:")
    for i, doc in enumerate(results["documents"]):
        distance = results["distances"][i]
        print(f"  {i+1}. (距离: {distance:.4f}) {doc}")
    print()


async def test_rag_service():
    """测试 RAG 服务"""
    print("=" * 50)
    print("测试 RAG 服务")
    print("=" * 50)
    
    # 索引一些测试数据
    # 领域知识
    await rag_service.index_knowledge(
        project_id=999,
        knowledge_id=1,
        term="VIP会员",
        definition="消费金额累计超过10000元的用户，享受9折优惠"
    )
    
    await rag_service.index_knowledge(
        project_id=999,
        knowledge_id=2,
        term="活跃用户",
        definition="最近30天内有下单记录的用户"
    )
    
    print("已索引 2 条领域知识")
    
    # 检索测试
    context = await rag_service.retrieve_context(
        query="查询所有VIP会员的订单",
        project_id=999,
        session_id=None,
        enable_history=False,
        enable_knowledge=True,
        enable_schema=False
    )
    
    print(f"\n查询: 查询所有VIP会员的订单")
    print(f"检索到 {len(context.relevant_knowledge)} 条相关知识:")
    for item in context.relevant_knowledge:
        print(f"  - {item['content']} (距离: {item['distance']:.4f})")
    print()


async def main():
    """主测试函数"""
    try:
        await test_embedding()
        await test_vector_db()
        await test_rag_service()
        print("=" * 50)
        print("所有测试完成!")
        print("=" * 50)
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
