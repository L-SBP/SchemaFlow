# src/backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(
    title="AI Database Platform - Chat Module",
    description="AI-powered database deployment and table generation - Chat Backend API",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 聊天API端点
@app.post("/api/v1/chat/chat")
async def chat_with_ai():
    """处理用户聊天消息 - Process user chat messages"""
    return {
        "response": "聊天后端服务运行正常！这是模拟响应。",
        "sql_generated": "SELECT * FROM users WHERE status = 'active'",
        "requires_confirmation": False,
        "statement_type": "SELECT",
        "statement_id": 1
    }

@app.get("/api/v1/chat/sessions/{session_id}/messages")
async def get_session_messages(session_id: int):
    """获取会话消息历史 - Get session message history"""
    return {
        "session_id": session_id,
        "messages": [
            {
                "message_id": 1,
                "message_type": "user",
                "content": "查询所有活跃用户",
                "requires_confirmation": False,
                "user_confirmed": None,
                "created_at": "2024-01-01T10:00:00Z"
            },
            {
                "message_id": 2, 
                "message_type": "assistant",
                "content": "已生成查询SQL",
                "requires_confirmation": False,
                "user_confirmed": None,
                "created_at": "2024-01-01T10:00:01Z"
            }
        ],
        "total_count": 2
    }

@app.post("/api/v1/chat/sessions")
async def create_session():
    """创建新会话 - Create new session"""
    return {
        "session_id": 1,
        "session_name": "新会话",
        "created_at": "2024-01-01T10:00:00Z",
        "last_activity": "2024-01-01T10:00:00Z"
    }

@app.get("/api/v1/chat/projects/{project_id}/sessions")
async def get_project_sessions(project_id: int):
    """获取项目所有会话 - Get all project sessions"""
    return [
        {
            "session_id": 1,
            "session_name": "数据分析会话",
            "created_at": "2024-01-01T10:00:00Z",
            "last_activity": "2024-01-01T10:00:00Z"
        },
        {
            "session_id": 2,
            "session_name": "用户查询会话", 
            "created_at": "2024-01-01T09:00:00Z",
            "last_activity": "2024-01-01T09:30:00Z"
        }
    ]

@app.get("/api/v1/chat/sessions/{session_id}")
async def get_session_detail(session_id: int):
    """获取会话详情 - Get session details"""
    return {
        "session_id": session_id,
        "session_name": f"Session {session_id}",
        "created_at": "2024-01-01T10:00:00Z",
        "last_activity": "2024-01-01T10:00:00Z"
    }

# 健康检查 - Health check
@app.get("/")
async def root():
    return {"message": "AI数据库平台聊天API服务运行中"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "chat-backend"}

if __name__ == "__main__":
    import uvicorn
    print("Starting AI Database Platform Chat Server...")
    print("API Documentation: http://localhost:8001/docs")
    print("Chat Endpoint: POST /api/v1/chat/chat")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)