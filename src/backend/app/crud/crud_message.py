from sqlalchemy.future import select
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# 导入两个模型
from models.message import Message
from models.ai_generated_statement import AIGeneratedStatement

class CRUDMessage:
    # 1. 创建一条新消息 (保持不变)
    async def create_message(self, db: AsyncSession, session_id: int, content: str, role: str) -> Message:
        db_obj = Message(
            session_id=session_id,
            content=content,
            message_type=role
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # 2. 获取最近的历史记录 (修改版：手动查询关联数据)
    async def get_recent_messages(self, db: AsyncSession, session_id: int, limit: int = 50) -> List[Message]:
        # A. 第一步：先只查消息表
        # 注意：这里去掉了 .options(selectinload(...))，解决了报错
        query = select(Message)\
            .filter(Message.session_id == session_id)\
            .order_by(desc(Message.created_at))\
            .limit(limit)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        if not messages:
            return []

        # B. 第二步：收集所有消息的 ID
        # 兼容处理：队友的模型主键可能叫 id，也可能叫 message_id
        message_ids = []
        for m in messages:
            # 优先取 message_id，如果没有就取 id
            mid = getattr(m, "message_id", getattr(m, "id", None))
            if mid:
                message_ids.append(mid)

        # C. 第三步：去查 SQL 语句表 (如果找到了消息ID)
        ai_statements = []
        if message_ids:
            stmt_query = select(AIGeneratedStatement).where(
                AIGeneratedStatement.message_id.in_(message_ids)
            )
            stmt_result = await db.execute(stmt_query)
            ai_statements = stmt_result.scalars().all()

        # D. 第四步：手动拼装 (把查到的 SQL 塞进消息对象里)
        # 制作一个字典方便查找： {message_id: [statement1, statement2]}
        stmt_map = {}
        for stmt in ai_statements:
            if stmt.message_id not in stmt_map:
                stmt_map[stmt.message_id] = []
            stmt_map[stmt.message_id].append(stmt)

        # 把 SQL 挂载到 Message 对象上 (临时属性)
        for m in messages:
            mid = getattr(m, "message_id", getattr(m, "id", None))
            # 我们给对象动态添加一个属性叫 ai_statement，这样 Endpoint 那边就不用改代码了
            m.ai_statement = stmt_map.get(mid, [])

        # 将倒序查询结果翻转为正序
        return list(reversed(messages))

# 实例化对象
crud_message = CRUDMessage()