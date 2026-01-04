"""
测试 Docker 模式下的 ChromaDB 连接。

运行方式：
    1. 先启动 ChromaDB 容器：docker-compose up chromadb -d
    2. 运行测试：python test_chroma_docker.py
"""

import asyncio


async def test_docker_mode():
    """测试 Docker 模式的 ChromaDB 连接"""
    print("=" * 60)
    print("测试 Docker 模式 ChromaDB 连接")
    print("=" * 60)
    
    import chromadb
    from chromadb.config import Settings
    
    # Docker 模式连接参数
    host = "localhost"  # 本地测试时使用 localhost
    port = 8100         # docker-compose 中映射的端口
    
    try:
        # 创建 HTTP 客户端
        client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 测试心跳
        heartbeat = client.heartbeat()
        print(f"✅ ChromaDB 服务连接成功!")
        print(f"   地址: {host}:{port}")
        print(f"   心跳: {heartbeat}")
        
        # 列出现有集合
        collections = client.list_collections()
        print(f"   现有集合数: {len(collections)}")
        
        print(f"\n✅ Docker 模式测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n提示：请确保 ChromaDB 容器已启动")
        print("      docker-compose up chromadb -d")
        return False


def test_embedded_mode():
    """测试内嵌模式（本地开发）"""
    print("\n" + "=" * 60)
    print("测试内嵌模式 ChromaDB（本地开发）")
    print("=" * 60)
    
    import chromadb
    from chromadb.config import Settings
    
    try:
        # 内嵌模式
        client = chromadb.Client(
            settings=Settings(anonymized_telemetry=False)
        )
        
        print(f"✅ ChromaDB 内嵌模式正常")
        print(f"   无需 Docker 容器")
        
        # 测试功能
        collection = client.get_or_create_collection("embed_test")
        collection.add(
            documents=["内嵌测试"],
            ids=["embed1"]
        )
        print(f"   集合功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 内嵌模式失败: {e}")
        return False


async def main():
    print("\n🔍 ChromaDB 连接测试\n")
    
    # 测试内嵌模式
    embedded_ok = test_embedded_mode()
    
    # 测试 Docker 模式
    docker_ok = await test_docker_mode()
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    print(f"   内嵌模式: {'✅ 通过' if embedded_ok else '❌ 失败'}")
    print(f"   Docker模式: {'✅ 通过' if docker_ok else '❌ 未启动/失败'}")
    
    if embedded_ok:
        print("\n💡 当前可用模式:")
        print("   - 本地开发：使用内嵌模式（config.yaml 中 use_http_client: false）")
        if docker_ok:
            print("   - Docker部署：使用HTTP客户端模式（config.yaml 中 use_http_client: true）")
        else:
            print("   - Docker部署：需先启动容器 `docker-compose up chromadb -d`")


if __name__ == "__main__":
    asyncio.run(main())
