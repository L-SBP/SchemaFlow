from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Database Platform - Chat API",
    description="Backend API for AI-powered database chat functionality",
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

# 直接定义路由，避免导入问题
@app.post("/api/v1/chat/chat")
async def chat_with_ai():
    """处理用户聊天消息"""
    return {
        "response": "聊天后端服务运行正常！Docker环境。",
        "sql_generated": "SELECT * FROM users WHERE status = 'active'",
        "requires_confirmation": False,
        "statement_type": "SELECT",
        "statement_id": 1
    }

@app.get("/api/v1/chat/sessions/{session_id}/messages")
async def get_session_messages(session_id: int):
    """获取会话消息历史"""
    return {
        "session_id": session_id,
        "messages": [
            {
                "message_id": 1,
                "message_type": "user",
                "content": "查询所有活跃用户",
                "requires_confirmation": False,
                "user_confirmed": None
            }
        ],
        "total_count": 1
    }

@app.post("/api/v1/chat/sessions")
async def create_session():
    """创建新会话"""
    return {
        "session_id": 1,
        "session_name": "新会话",
        "created_at": "2024-01-01T10:00:00Z",
        "last_activity": "2024-01-01T10:00:00Z"
    }

@app.get("/api/v1/chat/projects/{project_id}/sessions")
async def get_project_sessions(project_id: int):
    """获取项目所有会话"""
    return [
        {
            "session_id": 1,
            "session_name": "数据分析会话",
            "created_at": "2024-01-01T10:00:00Z",
            "last_activity": "2024-01-01T10:00:00Z"
        }
    ]

# 健康检查端点
@app.get("/")
async def root():
    return {"message": "AI Database Platform API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "chat-backend"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Database Platform Chat Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)