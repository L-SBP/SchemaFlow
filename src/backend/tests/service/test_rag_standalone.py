"""
RAG 功能独立测试脚本。

这个脚本可以直接运行，测试 Embedding 和 ChromaDB 是否正常工作。

运行方式：
    cd src/backend
    python -m tests.service.test_rag_standalone
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from openai import AsyncOpenAI
import chromadb
from chromadb.config import Settings
from app.config import settings

# 从配置文件获取 API key
EMBEDDING_API_KEY = settings.embedding.api_key
EMBEDDING_BASE_URL = settings.embedding.base_url
EMBEDDING_MODEL = settings.embedding.model
EMBEDDING_DIMENSIONS = settings.embedding.dimensions


# =========================================================
# 1. 测试 Embedding 服务（阿里云百炼）
# =========================================================

async def test_embedding():
    """测试 Embedding API 是否可用"""
    print("=" * 60)
    print("1. 测试 Embedding 服务（阿里云百炼 text-embedding-v4）")
    print("=" * 60)
    
    client = AsyncOpenAI(
        api_key=EMBEDDING_API_KEY,
        base_url=EMBEDDING_BASE_URL
    )
    
    test_text = "查询所有订单金额大于1000的用户"
    
    try:
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=test_text,
            dimensions=EMBEDDING_DIMENSIONS,
            encoding_format="float"
        )
        
        embedding = response.data[0].embedding
        print(f"✅ Embedding 服务正常")
        print(f"   输入文本: {test_text}")
        print(f"   向量维度: {len(embedding)}")
        print(f"   向量示例: [{embedding[0]:.6f}, {embedding[1]:.6f}, ...]")
        return True
        
    except Exception as e:
        print(f"❌ Embedding 服务失败: {e}")
        return False


# =========================================================
# 2. 测试 ChromaDB（内嵌模式，无需 Docker）
# =========================================================

def test_chromadb():
    """测试 ChromaDB 向量数据库"""
    print("\n" + "=" * 60)
    print("2. 测试 ChromaDB 向量数据库（内嵌模式）")
    print("=" * 60)
    
    try:
        # 创建内嵌模式客户端（数据存在内存，不持久化）
        client = chromadb.Client()
        
        # 创建或获取集合
        collection = client.get_or_create_collection(
            name="test_collection",
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"✅ ChromaDB 客户端创建成功")
        print(f"   模式: 内嵌模式（Embedded）")
        print(f"   无需 Docker 容器")
        
        # 添加测试数据
        collection.add(
            documents=["这是测试文档1", "这是测试文档2", "这是测试文档3"],
            metadatas=[{"type": "test"}, {"type": "test"}, {"type": "test"}],
            ids=["doc1", "doc2", "doc3"]
        )
        
        print(f"   添加文档数: 3")
        print(f"   集合文档总数: {collection.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB 测试失败: {e}")
        return False


# =========================================================
# 3. 测试完整 RAG 流程（Embedding + ChromaDB）
# =========================================================

async def test_full_rag():
    """测试完整的 RAG 流程"""
    print("\n" + "=" * 60)
    print("3. 测试完整 RAG 流程")
    print("=" * 60)
    
    client = AsyncOpenAI(
        api_key=EMBEDDING_API_KEY,
        base_url=EMBEDDING_BASE_URL
    )
    
    # 准备测试知识库
    knowledge_base = [
        {"term": "VIP会员", "definition": "消费金额累计超过10000元的用户，享受9折优惠"},
        {"term": "活跃用户", "definition": "最近30天内有下单记录的用户"},
        {"term": "新用户", "definition": "注册时间在7天内的用户"},
        {"term": "订单状态", "definition": "包括待支付、已支付、已发货、已完成、已取消"},
        {"term": "退款", "definition": "用户申请退还已支付的订单金额"},
    ]
    
    try:
        # 1. 生成知识库向量
        print("   步骤1: 生成知识库向量...")
        texts = [f"{k['term']}: {k['definition']}" for k in knowledge_base]
        
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
            dimensions=EMBEDDING_DIMENSIONS,
            encoding_format="float"
        )
        
        embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        print(f"   ✅ 生成 {len(embeddings)} 条知识向量")
        
        # 2. 存入 ChromaDB
        print("   步骤2: 存入 ChromaDB...")
        chroma_client = chromadb.Client()
        collection = chroma_client.get_or_create_collection(
            name="rag_test",
            metadata={"hnsw:space": "cosine"}
        )
        
        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=[{"term": k["term"]} for k in knowledge_base],
            ids=[f"k{i}" for i in range(len(knowledge_base))]
        )
        print(f"   ✅ 存入 {collection.count()} 条记录")
        
        # 3. 测试查询
        print("   步骤3: 测试语义检索...")
        query = "查询消费金额高的用户"
        
        # 生成查询向量
        query_response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query,
            dimensions=EMBEDDING_DIMENSIONS,
            encoding_format="float"
        )
        query_embedding = query_response.data[0].embedding
        
        # 检索
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        print(f"\n   查询: \"{query}\"")
        print(f"   检索结果 (Top 3):")
        for i, doc in enumerate(results["documents"][0]):
            distance = results["distances"][0][i]
            similarity = 1 - distance  # 余弦距离转相似度
            print(f"      {i+1}. [相似度: {similarity:.2%}] {doc}")
        
        print(f"\n✅ RAG 流程测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ RAG 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# =========================================================
# 主函数
# =========================================================

async def main():
    print("\n" + "🚀 RAG 功能测试开始 " + "=" * 40 + "\n")
    
    results = []
    
    # 测试 1: Embedding
    results.append(("Embedding 服务", await test_embedding()))
    
    # 测试 2: ChromaDB
    results.append(("ChromaDB", test_chromadb()))
    
    # 测试 3: 完整 RAG
    results.append(("完整 RAG 流程", await test_full_rag()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + ("🎉 所有测试通过！RAG 功能可正常使用。" if all_passed else "⚠️ 部分测试失败，请检查配置。"))
    print()


if __name__ == "__main__":
    asyncio.run(main())
