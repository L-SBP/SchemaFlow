"""
RAG 效果测试脚本。

测试 RAG 检索的实际效果，包括：
1. 领域知识检索 - 测试业务术语匹配准确度
2. DDL 检索 - 测试表结构匹配准确度
3. 历史对话检索 - 测试相似问题匹配

运行方式：
    cd src/backend
    python -m tests.service.test_rag_effect
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.service.embedding_service import embedding_service
from app.service.vector_db_service import vector_db_service, VectorDBService
from app.service.rag_service import rag_service, RAGContext


# =========================================================
# 测试数据
# =========================================================

# 模拟的领域知识（业务术语）
MOCK_KNOWLEDGE = [
    {"id": 1, "term": "VIP会员", "definition": "消费金额累计超过10000元的用户，享受9折优惠和优先客服"},
    {"id": 2, "term": "活跃用户", "definition": "最近30天内有登录或下单记录的用户"},
    {"id": 3, "term": "流失用户", "definition": "超过90天没有任何活动记录的用户"},
    {"id": 4, "term": "新用户", "definition": "注册时间在7天内的用户，首单享受8折优惠"},
    {"id": 5, "term": "订单状态", "definition": "订单的生命周期状态，包括：待支付、已支付、已发货、已完成、已取消、已退款"},
    {"id": 6, "term": "GMV", "definition": "Gross Merchandise Volume，成交总额，指平台在一定时间内的总销售金额"},
    {"id": 7, "term": "客单价", "definition": "每位顾客平均购买金额，计算方式为总销售额除以订单数"},
    {"id": 8, "term": "复购率", "definition": "在一定时间内再次购买的用户占总用户的比例"},
    {"id": 9, "term": "退款率", "definition": "退款订单数占总订单数的比例，反映商品质量和服务水平"},
    {"id": 10, "term": "库存周转率", "definition": "一定时期内库存周转次数，计算方式为销售成本除以平均库存"},
]

# 模拟的 DDL（表结构）
MOCK_DDL = """
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    is_vip BOOLEAN DEFAULT FALSE,
    total_spent DECIMAL(10,2) DEFAULT 0,
    status ENUM('active', 'inactive', 'banned') DEFAULT 'active'
);

CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    cost DECIMAL(10,2),
    category_id INT,
    stock_quantity INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    order_no VARCHAR(50) NOT NULL UNIQUE,
    total_amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'paid', 'shipped', 'completed', 'cancelled', 'refunded') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    shipped_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE order_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    parent_id INT,
    level INT DEFAULT 1,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);

CREATE TABLE inventory_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    change_quantity INT NOT NULL,
    change_type ENUM('in', 'out', 'adjust') NOT NULL,
    reason VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE refunds (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    reason TEXT,
    status ENUM('pending', 'approved', 'rejected', 'completed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
"""

# 模拟的历史对话
MOCK_HISTORY = [
    {"id": 1, "role": "user", "content": "查询所有VIP用户的订单总金额"},
    {"id": 2, "role": "assistant", "content": "SELECT u.username, SUM(o.total_amount) as total FROM users u JOIN orders o ON u.id = o.user_id WHERE u.is_vip = TRUE GROUP BY u.id"},
    {"id": 3, "role": "user", "content": "统计每个月的销售额"},
    {"id": 4, "role": "assistant", "content": "SELECT DATE_FORMAT(created_at, '%Y-%m') as month, SUM(total_amount) as monthly_sales FROM orders WHERE status = 'completed' GROUP BY month"},
    {"id": 5, "role": "user", "content": "找出库存少于10的商品"},
    {"id": 6, "role": "assistant", "content": "SELECT * FROM products WHERE stock_quantity < 10 AND is_active = TRUE"},
    {"id": 7, "role": "user", "content": "计算用户的复购率"},
    {"id": 8, "role": "assistant", "content": "SELECT COUNT(DISTINCT CASE WHEN order_count > 1 THEN user_id END) / COUNT(DISTINCT user_id) as repurchase_rate FROM (SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id) t"},
]

# 测试查询和期望结果
TEST_QUERIES = [
    {
        "query": "查询VIP用户的消费情况",
        "expected_knowledge": ["VIP会员"],
        "expected_tables": ["users", "orders"],
        "description": "应该匹配VIP会员定义和用户、订单表"
    },
    {
        "query": "统计这个月的GMV",
        "expected_knowledge": ["GMV"],
        "expected_tables": ["orders"],
        "description": "应该匹配GMV定义和订单表"
    },
    {
        "query": "找出流失的客户",
        "expected_knowledge": ["流失用户"],
        "expected_tables": ["users"],
        "description": "应该匹配流失用户定义和用户表"
    },
    {
        "query": "库存不足的商品有哪些",
        "expected_knowledge": ["库存周转率"],
        "expected_tables": ["products", "inventory_logs"],
        "description": "应该匹配库存相关术语和商品、库存表"
    },
    {
        "query": "退款订单的统计",
        "expected_knowledge": ["退款率", "订单状态"],
        "expected_tables": ["orders", "refunds"],
        "description": "应该匹配退款相关术语和订单、退款表"
    },
    {
        "query": "新用户的首单优惠",
        "expected_knowledge": ["新用户"],
        "expected_tables": ["users", "orders"],
        "description": "应该匹配新用户定义"
    },
]


# =========================================================
# 测试函数
# =========================================================

PROJECT_ID = 99999  # 测试用项目ID
SESSION_ID = 88888  # 测试用会话ID


async def setup_test_data():
    """准备测试数据：将知识、DDL、历史写入向量数据库"""
    print("=" * 70)
    print("📦 准备测试数据")
    print("=" * 70)
    
    # 1. 索引领域知识
    print("\n1️⃣  索引领域知识...")
    for k in MOCK_KNOWLEDGE:
        await rag_service.index_knowledge(
            project_id=PROJECT_ID,
            knowledge_id=k["id"],
            term=k["term"],
            definition=k["definition"]
        )
    print(f"   ✅ 已索引 {len(MOCK_KNOWLEDGE)} 条领域知识")
    
    # 2. 索引 DDL
    print("\n2️⃣  索引 DDL（表结构）...")
    await rag_service.index_ddl(
        project_id=PROJECT_ID,
        ddl_text=MOCK_DDL
    )
    print(f"   ✅ 已索引 DDL")
    
    # 3. 索引历史对话
    print("\n3️⃣  索引历史对话...")
    for msg in MOCK_HISTORY:
        await rag_service.index_message(
            session_id=SESSION_ID,
            message_id=msg["id"],
            content=msg["content"],
            role=msg["role"]
        )
    print(f"   ✅ 已索引 {len(MOCK_HISTORY)} 条历史消息")
    
    print("\n" + "=" * 70)


async def test_knowledge_retrieval():
    """测试领域知识检索效果"""
    print("\n" + "=" * 70)
    print("🔍 测试1: 领域知识检索")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(TEST_QUERIES, 1):
        query = test["query"]
        expected = test["expected_knowledge"]
        
        print(f"\n📝 测试 {i}: {query}")
        print(f"   期望匹配: {expected}")
        
        # 检索
        context = await rag_service.retrieve_context(
            query=query,
            project_id=PROJECT_ID,
            enable_history=False,
            enable_knowledge=True,
            enable_ddl=False,
            knowledge_top_k=3
        )
        
        # 提取检索到的术语
        retrieved_terms = [
            r.get("metadata", {}).get("term", "")
            for r in context.relevant_knowledge
        ]
        
        print(f"   实际检索: {retrieved_terms}")
        
        # 检查是否匹配
        matched = any(exp in retrieved_terms for exp in expected)
        if matched:
            print(f"   ✅ 通过")
            passed += 1
        else:
            print(f"   ❌ 未匹配到期望术语")
            failed += 1
    
    print(f"\n📊 领域知识检索结果: {passed}/{passed+failed} 通过")
    return passed, failed


async def test_ddl_retrieval():
    """测试 DDL 检索效果"""
    print("\n" + "=" * 70)
    print("🔍 测试2: DDL（表结构）检索")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(TEST_QUERIES, 1):
        query = test["query"]
        expected = test["expected_tables"]
        
        print(f"\n📝 测试 {i}: {query}")
        print(f"   期望表: {expected}")
        
        # 检索
        context = await rag_service.retrieve_context(
            query=query,
            project_id=PROJECT_ID,
            enable_history=False,
            enable_knowledge=False,
            enable_ddl=True,
            ddl_top_k=3
        )
        
        # 提取检索到的表名
        retrieved_tables = [
            r.get("metadata", {}).get("table_name", "")
            for r in context.relevant_ddl
        ]
        
        print(f"   实际检索: {retrieved_tables}")
        
        # 检查是否匹配
        matched = any(exp in retrieved_tables for exp in expected)
        if matched:
            print(f"   ✅ 通过")
            passed += 1
        else:
            print(f"   ❌ 未匹配到期望表")
            failed += 1
    
    print(f"\n📊 DDL检索结果: {passed}/{passed+failed} 通过")
    return passed, failed


async def test_history_retrieval():
    """测试历史对话检索效果"""
    print("\n" + "=" * 70)
    print("🔍 测试3: 历史对话检索")
    print("=" * 70)
    
    test_queries = [
        {"query": "VIP客户的订单", "expected_contains": "VIP"},
        {"query": "每月销售统计", "expected_contains": "月"},
        {"query": "库存预警", "expected_contains": "库存"},
        {"query": "用户复购分析", "expected_contains": "复购"},
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_queries, 1):
        query = test["query"]
        expected = test["expected_contains"]
        
        print(f"\n📝 测试 {i}: {query}")
        print(f"   期望包含: '{expected}'")
        
        # 检索
        context = await rag_service.retrieve_context(
            query=query,
            project_id=PROJECT_ID,
            session_id=SESSION_ID,
            enable_history=True,
            enable_knowledge=False,
            enable_ddl=False,
            history_top_k=2
        )
        
        # 显示检索结果
        for j, h in enumerate(context.relevant_history[:2], 1):
            content = h.get("content", "")[:60]
            distance = h.get("distance", 0)
            print(f"   [{j}] (距离:{distance:.3f}) {content}...")
        
        # 检查是否匹配
        matched = any(
            expected in h.get("content", "")
            for h in context.relevant_history
        )
        
        if matched:
            print(f"   ✅ 通过")
            passed += 1
        else:
            print(f"   ❌ 未匹配")
            failed += 1
    
    print(f"\n📊 历史检索结果: {passed}/{passed+failed} 通过")
    return passed, failed


async def test_combined_retrieval():
    """测试综合检索（模拟实际使用场景）"""
    print("\n" + "=" * 70)
    print("🔍 测试4: 综合检索（实际场景模拟）")
    print("=" * 70)
    
    query = "帮我查询所有VIP用户上个月的订单金额，按金额降序排列"
    
    print(f"\n📝 用户查询: {query}")
    
    context = await rag_service.retrieve_context(
        query=query,
        project_id=PROJECT_ID,
        session_id=SESSION_ID,
        enable_history=True,
        enable_knowledge=True,
        enable_ddl=True,
        history_top_k=3,
        knowledge_top_k=3,
        ddl_top_k=5
    )
    
    print("\n📚 检索到的领域知识:")
    for k in context.relevant_knowledge:
        term = k.get("metadata", {}).get("term", "")
        dist = k.get("distance", 0)
        print(f"   - {term} (距离: {dist:.3f})")
    
    print("\n📋 检索到的相关表:")
    for d in context.relevant_ddl:
        table = d.get("metadata", {}).get("table_name", "")
        dist = d.get("distance", 0)
        print(f"   - {table} (距离: {dist:.3f})")
    
    print("\n💬 检索到的历史对话:")
    for h in context.relevant_history:
        content = h.get("content", "")[:50]
        role = h.get("metadata", {}).get("role", "")
        dist = h.get("distance", 0)
        print(f"   - [{role}] {content}... (距离: {dist:.3f})")
    
    # 构建 Prompt 示例
    print("\n" + "-" * 50)
    print("💡 构建的 RAG Prompt 示例:")
    print("-" * 50)
    
    prompt_parts = []
    
    if context.relevant_knowledge:
        prompt_parts.append("【业务术语说明】")
        for k in context.relevant_knowledge:
            term = k.get("metadata", {}).get("term", "")
            content = k.get("content", "")
            prompt_parts.append(f"- {content}")
    
    if context.relevant_ddl:
        prompt_parts.append("\n【相关表结构】")
        for d in context.relevant_ddl[:3]:  # 只取前3个
            content = d.get("content", "")
            prompt_parts.append(content)
    
    if context.relevant_history:
        prompt_parts.append("\n【相关历史问答】")
        for h in context.relevant_history:
            role = h.get("metadata", {}).get("role", "")
            content = h.get("content", "")
            prompt_parts.append(f"[{role}]: {content}")
    
    prompt_parts.append(f"\n【用户问题】\n{query}")
    
    full_prompt = "\n".join(prompt_parts)
    print(full_prompt[:1500] + "..." if len(full_prompt) > 1500 else full_prompt)


async def cleanup_test_data():
    """清理测试数据"""
    print("\n" + "=" * 70)
    print("🧹 清理测试数据")
    print("=" * 70)
    
    try:
        await rag_service.delete_project_knowledge(PROJECT_ID)
        print("   ✅ 已删除领域知识")
    except Exception as e:
        print(f"   ⚠️ 删除领域知识失败: {e}")
    
    try:
        await rag_service.delete_project_ddl(PROJECT_ID)
        print("   ✅ 已删除 DDL")
    except Exception as e:
        print(f"   ⚠️ 删除 DDL 失败: {e}")
    
    try:
        await rag_service.delete_session_history(SESSION_ID)
        print("   ✅ 已删除历史对话")
    except Exception as e:
        print(f"   ⚠️ 删除历史对话失败: {e}")


async def main():
    """主测试函数"""
    print("\n" + "🚀" * 35)
    print("              RAG 效果测试")
    print("🚀" * 35)
    
    try:
        # 准备数据
        await setup_test_data()
        
        # 等待向量数据库索引完成
        await asyncio.sleep(1)
        
        # 运行测试
        k_passed, k_failed = await test_knowledge_retrieval()
        d_passed, d_failed = await test_ddl_retrieval()
        h_passed, h_failed = await test_history_retrieval()
        
        # 综合测试
        await test_combined_retrieval()
        
        # 汇总结果
        total_passed = k_passed + d_passed + h_passed
        total_failed = k_failed + d_failed + h_failed
        
        print("\n" + "=" * 70)
        print("📊 测试汇总")
        print("=" * 70)
        print(f"   领域知识检索: {k_passed}/{k_passed+k_failed} 通过")
        print(f"   DDL 检索:     {d_passed}/{d_passed+d_failed} 通过")
        print(f"   历史对话检索: {h_passed}/{h_passed+h_failed} 通过")
        print(f"   ---")
        print(f"   总计: {total_passed}/{total_passed+total_failed} 通过")
        
        if total_failed == 0:
            print("\n   🎉 所有测试通过！RAG 检索效果良好")
        else:
            print(f"\n   ⚠️ 有 {total_failed} 个测试未通过，可能需要调整相似度阈值")
        
    finally:
        # 清理数据
        await cleanup_test_data()
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
