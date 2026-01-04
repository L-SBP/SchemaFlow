"""
消息 CRUD。

本模块提供聊天消息和历史记录管理的 CRUD 操作。
"""

# backend/app/crud/crud_message.py

from sqlalchemy.future import select
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# 导入两个模型
from models.message import Message
from models.ai_generated_statement import AIGeneratedStatement

class CRUDMessage:
    """
    消息数据操作类。

    提供消息的创建和历史记录查询功能。
    """

    async def create_message(self, db: AsyncSession, session_id: int, content: str, role: str) -> Message:
        """
        创建一条新消息。

        Args:
            db (AsyncSession): 数据库会话。
            session_id (int): 会话 ID。
            content (str): 消息内容。
            role (str): 消息角色 (user/assistant)。

        Returns:
            Message: 创建的消息对象。
        """
        db_obj = Message(
            session_id=session_id,
            content=content,
            message_type=role
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # backend/app/crud/crud_message.py

# backend/app/crud/crud_message.py

    async def get_recent_messages(self, db: AsyncSession, session_id: int, limit: int = 50) -> List[Message]:
        """
        获取最近的历史记录，并直接映射 SQL 执行结果。
        """
        # 1. 查消息基础信息
        query = select(Message)\
            .filter(Message.session_id == session_id)\
            .order_by(desc(Message.created_at))\
            .limit(limit)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        if not messages:
            return []

        # 2. 收集消息 ID
        message_ids = [getattr(m, "message_id", getattr(m, "id", None)) for m in messages]

        # 3. 查关联的 SQL 详情和结果 (来自 ai_generated_statement 表)
        stmt_map = {}
        if message_ids:
            # 获取 SQL 文本、类型和执行结果 [cite: 638, 811-820]
            stmt_query = select(AIGeneratedStatement).where(
                AIGeneratedStatement.message_id.in_(message_ids)
            )
            stmt_result = await db.execute(stmt_query)
            ai_statements = stmt_result.scalars().all()
            
            # 建立 ID 映射
            for stmt in ai_statements:
                stmt_map[stmt.message_id] = stmt

        # 4. 【核心修复】：直接映射到 ChatResponse 需要的字段
        for m in messages:
            mid = getattr(m, "message_id", getattr(m, "id", None))
            stmt = stmt_map.get(mid)
            
            if stmt:
                # 直接给对象赋值，名称必须与 ChatResponse 中的定义一致
                m.sql_text = stmt.sql_text
                m.sql_type = stmt.statement_type
                # 这里的 .data 对应 ai_generated_statement 表的 execution_result 字段 [cite: 818, 830]
                m.data = stmt.execution_result 
            else:
                # 对于 user 消息或没有 SQL 的消息，设为空
                m.sql_text = None
                m.sql_type = "UNKNOWN"
                m.data = None

        # 5. 返回正序列表，满足历史加载需求
        return list(reversed(messages))

# 实例化对象
crud_message = CRUDMessage()