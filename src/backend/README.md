# Backend 后端服务

基于 FastAPI + Celery 的异步后端服务，支持多数据库（PostgreSQL、MySQL、SQLite）、AI 对话、异步任务队列等功能。

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.104.1 | Web 框架 |
| SQLAlchemy | 2.0.23 | ORM |
| PostgreSQL | - | 主数据库 |
| MySQL | - | 用户项目数据库 |
| SQLite | - | 用户项目数据库 |
| Redis | 4.6.0 | 缓存 & Celery Broker |
| Celery | 5.3.4 | 异步任务队列 |
| Pydantic | 2.4.2 | 数据验证 |

## 目录结构

```
src/backend/
├── app/                          # 应用主目录
│   ├── main.py                   # 启动入口
│   ├── server.py                 # FastAPI 应用配置
│   ├── celery_app.py             # Celery 配置
│   │
│   ├── api/                      # API 路由
│   │   └── v1/
│   │       ├── api.py            # 路由汇总
│   │       └── endpoints/        # 各模块路由
│   │
│   ├── config/                   # 配置管理
│   │   └── base.py               # 配置基类
│   │
│   ├── core/                     # 核心模块
│   │   ├── config.py             # 应用配置
│   │   ├── database.py           # 数据库连接
│   │   ├── deps.py               # 依赖注入
│   │   ├── security.py           # 安全模块
│   │   ├── auth.py               # 认证模块
│   │   ├── exceptions.py         # 自定义异常
│   │   ├── exception_handlers.py # 异常处理器
│   │   └── log.py                # 日志配置
│   │
│   ├── crud/                     # 数据访问层
│   │   └── crud_*.py             # CRUD 操作
│   │
│   ├── models/                   # 数据模型 (SQLAlchemy)
│   │
│   ├── schema/                   # 请求/响应模型 (Pydantic)
│   │
│   ├── service/                  # 业务逻辑层
│   │   ├── ai_service.py         # AI 服务
│   │   ├── chat_service.py       # 对话服务
│   │   ├── project_service.py    # 项目服务
│   │   ├── mysql_service.py      # MySQL 服务
│   │   └── ...
│   │
│   ├── tasks/                    # Celery 异步任务
│   │   ├── __init__.py
│   │   └── ai_generation_tasks.py # AI 生成任务
│   │
│   ├── mysql/                    # MySQL 相关
│   ├── postgresql/               # PostgreSQL 相关
│   ├── sqlite/                   # SQLite 相关
│   ├── redis_client/             # Redis 客户端
│   └── ai/                       # AI 模块
│
├── tests/                        # 测试目录
├── logs/                         # 日志目录
├── static/                       # 静态文件
├── config.yaml                   # 配置文件
├── requirements.txt              # Python 依赖
└── Dockerfile.dev                # Docker 开发配置
```

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml` 配置文件：

```yaml
# 数据库配置
db:
  host: localhost
  port: 5432
  database: your_database
  username: your_username
  password: your_password

# MySQL 配置（用户项目数据库）
mysql:
  host: localhost
  port: 3306
  username: root
  password: your_password

# Redis 配置
redis:
  host: localhost
  port: 6379

# 应用配置
app:
  host: 0.0.0.0
  port: 8000
  reload: true
```

### 3. 启动服务

```bash
cd src/backend/app

# 启动 FastAPI 服务
python main.py

# 或使用 uvicorn
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 启动 Celery Worker

```bash
cd src/backend/app

# Windows（必须使用 --pool=solo）
celery -A celery_app worker --loglevel=info --pool=solo

# Linux/Mac
celery -A celery_app worker --loglevel=info --concurrency=4
```

### 5. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发指南

### 添加新的 API 路由

1. 在 `api/v1/endpoints/` 下创建新文件
2. 在 `api/v1/api.py` 中注册路由

```python
# api/v1/endpoints/my_module.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_items():
    return {"items": []}
```

```python
# api/v1/api.py
from api.v1.endpoints import my_module

api_router.include_router(
    my_module.router,
    prefix="/my-module",
    tags=["My Module"]
)
```

### 添加新的 Celery 任务

详见 [Celery 任务迁移文档](celery任务迁移文档.md) 中的"开发者指南"部分。

**基本步骤：**

1. 在 `tasks/` 目录下创建任务文件
2. 在 `celery_app.py` 的 `include` 列表中注册
3. **重启 Celery Worker**

```python
# tasks/my_tasks.py
from celery_app import celery_app

@celery_app.task(name="tasks.my_task", bind=True)
def my_task(self, param1: str):
    # 任务逻辑
    return {"success": True}
```

```python
# celery_app.py
celery_app = Celery(
    "app",
    include=[
        "tasks.ai_generation_tasks",
        "tasks.my_tasks",  # 新增
    ]
)
```

### 数据库操作

使用 SQLAlchemy 异步 Session：

```python
from sqlalchemy.ext.asyncio import AsyncSession
from core.deps import get_db

@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

### 依赖注入

常用依赖：

```python
from core.deps import (
    get_db,                  # 数据库 Session
    get_current_user,        # 当前登录用户
    get_current_admin,       # 当前管理员用户
    get_mysql_instance,      # MySQL 实例
    get_postgres_instance,   # PostgreSQL 实例
    get_sqlite_instance,     # SQLite 实例
)
```

## 测试

```bash
cd src/backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/service/test_chat_service.py

# 带覆盖率报告
pytest --cov=app --cov-report=html
```

## 常见问题

### Q: Windows 启动 Celery Worker 报错

使用 `--pool=solo` 参数：

```bash
celery -A celery_app worker --loglevel=info --pool=solo
```

### Q: 修改 Celery 任务后不生效

**必须重启 Celery Worker**。Celery Worker 在启动时加载任务代码，修改后不会自动热重载。

### Q: 数据库连接池耗尽

检查是否正确关闭 Session：

```python
async with get_session(engine) as session:
    # 操作完成后自动关闭
    pass
```

### Q: Redis 连接失败

1. 确认 Redis 服务正在运行
2. 检查 `config.yaml` 中的 Redis 配置
3. 检查防火墙设置

## 相关文档

- [Celery 任务迁移文档](celery任务迁移文档.md)
- [Redis 缓存设计文档](../../doc/project/02-设计文档/redis缓存设计文档.md)
- [API 接口文档](http://localhost:8000/docs)
