from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import sqlparse

# 使用模拟数据库
from src.backend.app.core.database import get_mock_db, AsyncSession as MockAsyncSession

class ChatService:
    def __init__(self, db: MockAsyncSession):
        self.db = db
    
    async def process_user_message(
        self, 
        user_message: str, 
        session_id: int, 
        project_id: int
    ) -> Dict[str, Any]:
        """处理用户消息的核心方法（模拟版本）"""
        
        print(f"[ChatService] 处理消息: session={session_id}, project={project_id}")
        print(f"[ChatService] 用户消息: {user_message}")
        
        # 1. 模拟保存用户消息
        user_msg_id = await self._mock_save_user_message(session_id, user_message)
        
        # 2. 模拟获取对话上下文
        conversation_history = await self._mock_get_conversation_context(session_id)
        
        # 3. 模拟获取业务术语
        domain_terms = await self._mock_get_domain_terms(project_id)
        
        # 4. 调用AI生成SQL（模拟）
        ai_result = await self._generate_sql_with_ai(
            user_message, 
            conversation_history, 
            domain_terms
        )
        
        # 5. 模拟保存AI生成的SQL
        statement_id = await self._mock_save_ai_statement(user_msg_id, ai_result)
        
        # 6. 分析SQL类型
        sql_type = self._analyze_sql_type(ai_result["sql"])
        
        # 7. 模拟更新会话活动时间
        await self._mock_update_session_activity(session_id)
        
        return {
            "response": ai_result.get("explanation", "SQL已生成（模拟模式）"),
            "sql_generated": ai_result["sql"],
            "statement_type": sql_type,
            "requires_confirmation": sql_type in ["INSERT", "UPDATE", "DELETE"],
            "statement_id": statement_id
        }
    
    async def _mock_save_user_message(self, session_id: int, content: str) -> int:
        """模拟保存用户消息"""
        print(f"[Mock] 保存用户消息: session={session_id}, content={content}")
        return 1  # 返回模拟的消息ID
    
    async def _mock_get_conversation_context(self, session_id: int) -> List[Dict[str, str]]:
        """模拟获取对话上下文"""
        print(f"[Mock] 获取对话上下文: session={session_id}")
        return [
            {"role": "user", "content": "之前的用户消息"},
            {"role": "assistant", "content": "之前的AI回复"}
        ]
    
    async def _mock_get_domain_terms(self, project_id: int) -> List[Dict[str, str]]:
        """模拟获取业务术语"""
        print(f"[Mock] 获取业务术语: project={project_id}")
        return [
            {"term": "用户", "definition": "系统的使用者"},
            {"term": "订单", "definition": "客户购买商品的记录"}
        ]
    
    async def _generate_sql_with_ai(
        self, 
        user_message: str, 
        conversation_history: List[Dict[str, str]],
        domain_terms: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """调用AI生成SQL（模拟版本）"""
        print(f"[Mock] 生成SQL: 使用{len(domain_terms)}个业务术语")
        
        # 基于用户消息内容生成不同的模拟SQL
        user_message_lower = user_message.lower()
        
        if any(word in user_message_lower for word in ["查询", "查看", "select", "find"]):
            return {
                "sql": "SELECT id, name, email FROM users WHERE status = 'active'",
                "type": "SELECT",
                "explanation": "查询活跃用户信息"
            }
        elif any(word in user_message_lower for word in ["更新", "修改", "update", "change"]):
            return {
                "sql": "UPDATE products SET price = 99.99 WHERE id = 123",
                "type": "UPDATE", 
                "explanation": "更新产品价格，请确认执行"
            }
        elif any(word in user_message_lower for word in ["插入", "添加", "insert", "add"]):
            return {
                "sql": "INSERT INTO orders (user_id, product_id, quantity) VALUES (1, 456, 2)",
                "type": "INSERT",
                "explanation": "添加新订单，请确认执行"
            }
        elif any(word in user_message_lower for word in ["删除", "remove", "delete"]):
            return {
                "sql": "DELETE FROM logs WHERE created_at < '2024-01-01'",
                "type": "DELETE",
                "explanation": "删除旧日志，请确认执行"
            }
        else:
            return {
                "sql": "SELECT COUNT(*) as total_users FROM users",
                "type": "SELECT",
                "explanation": "统计用户总数"
            }
    
    async def _mock_save_ai_statement(
        self, 
        message_id: int, 
        ai_result: Dict[str, Any]
    ) -> int:
        """模拟保存AI生成的SQL"""
        print(f"[Mock] 保存AI语句: message={message_id}, sql={ai_result['sql']}")
        return 1  # 返回模拟的语句ID
    
    def _analyze_sql_type(self, sql: str) -> str:
        """分析SQL类型"""
        try:
            parsed = sqlparse.parse(sql)
            if parsed:
                first_token = parsed[0].token_first(skip_cm=True)
                if first_token:
                    return first_token.normalized.upper()
        except:
            pass
        return "UNKNOWN"
    
    async def _mock_update_session_activity(self, session_id: int):
        """模拟更新会话活动时间"""
        print(f"[Mock] 更新会话活动时间: session={session_id}")