# Celery 任务迁移文档

## 概述

本次重构将 Schema、DDL、ER 图生成逻辑从 FastAPI BackgroundTasks 迁移到 Celery 异步任务队列，提供更好的任务管理、重试机制和状态跟踪能力。

## 核心设计理念：每步持久化

**每个生成阶段完成后立即保存到数据库**，用户可以随时中断，之后回来继续流程：

| 阶段 | 保存内容 | 数据库字段 | 用户可中断后继续 |
|------|---------|-----------|----------------|
| Schema 生成 | Schema 文本 | `schema_definition['schema']` | ✅ 回来后可查看/修改 Schema |
| ER 图生成 | Mermaid 代码 | `er_diagram_code` | ✅ 回来后可查看 ER 图 |
| DDL 生成 | DDL 语句 | `ddl_statement` | ✅ 回来后可查看/修改 DDL |

**用户场景示例：**
1. 用户创建项目后离开 → Schema 和 ER 图已保存
2. 隔天回来 → 通过项目详情接口获取已生成的 Schema
3. 确认 Schema → 触发 DDL 生成
4. 又离开 → DDL 已保存
5. 再回来 → 获取已生成的 DDL，确认后部署

---

## 开发者指南：如何添加新的 Celery 任务

### 步骤 1：创建任务文件或在现有文件中添加任务

任务文件位置：`src/backend/app/tasks/`

**创建新任务文件示例：**

```python
# backend/app/tasks/my_new_tasks.py

"""
新任务模块

在此添加模块说明
"""

import asyncio
from celery import shared_task
from celery.utils.log import get_task_logger

from celery_app import celery_app
from core.config import config
from core.database import PsqlHelper

logger = get_task_logger(__name__)


# =========================================================
# 辅助函数：同步运行异步代码
# =========================================================

def run_async(coro):
    """
    在同步环境中运行异步协程。
    
    Celery Worker 是同步的，需要用此方法包装异步代码。
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# =========================================================
# 任务定义
# =========================================================

@celery_app.task(
    name="tasks.my_task",           # 任务名称（必须唯一）
    bind=True,                       # 绑定 self，可访问任务实例
    max_retries=3,                   # 最大重试次数
    default_retry_delay=30,          # 重试间隔（秒）
    soft_time_limit=300,             # 软超时（秒）- 触发 SoftTimeLimitExceeded
    time_limit=360,                  # 硬超时（秒）- 强制终止
)
def my_task(self, param1: str, param2: int) -> dict:
    """
    我的新任务
    
    Args:
        self: Celery 任务实例（bind=True 时可用）
        param1: 参数1
        param2: 参数2
        
    Returns:
        dict: 任务执行结果
    """
    logger.info(f"[Task] Starting my_task with param1={param1}, param2={param2}")
    
    try:
        # 执行异步代码
        result = run_async(_async_business_logic(param1, param2))
        
        logger.info(f"[Task] my_task completed successfully")
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"[Task] my_task failed: {e}")
        
        # 可选：触发重试
        # raise self.retry(exc=e, countdown=30)
        
        return {
            "success": False,
            "error": str(e)
        }


async def _async_business_logic(param1: str, param2: int):
    """异步业务逻辑（内部实现）"""
    # 如果需要数据库操作，创建临时引擎
    temp_engine = PsqlHelper._get_async_engine(config.db)
    try:
        async with PsqlHelper.get_session(temp_engine) as session:
            # 执行数据库操作
            pass
        return "success"
    finally:
        await temp_engine.dispose()
```

### 步骤 2：注册任务模块到 Celery

编辑 `celery_app.py`，在 `include` 列表中添加新模块：

```python
# backend/app/celery_app.py

celery_app = Celery(
    "app",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "tasks.ai_generation_tasks",   # 已有的 AI 生成任务
        "tasks.my_new_tasks",          # 新增：我的新任务模块
    ]
)
```

### 步骤 3：在 Service 层调用任务

```python
# backend/app/service/my_service.py

from tasks.my_new_tasks import my_task

def trigger_my_task(param1: str, param2: int) -> str:
    """
    触发异步任务
    
    Returns:
        str: Celery 任务 ID
    """
    task = my_task.delay(param1, param2)
    return task.id


def get_task_result(task_id: str) -> dict:
    """
    查询任务状态和结果
    """
    from celery.result import AsyncResult
    from celery_app import celery_app
    
    result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "status": result.status,      # PENDING, STARTED, SUCCESS, FAILURE, RETRY
        "ready": result.ready(),      # 是否完成
        "successful": result.successful() if result.ready() else None,
        "result": result.result if result.ready() else None,
    }
```

### 步骤 4：重启 Celery Worker

**⚠️ 重要：修改任务代码后必须重启 Worker！**

```bash
# 停止当前 Worker (Ctrl+C)

# 重新启动
cd src/backend/app
celery -A celery_app worker --loglevel=info --pool=solo  # Windows
celery -A celery_app worker --loglevel=info              # Linux/Mac
```

### 常用任务装饰器参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `name` | 任务名称（全局唯一） | `"tasks.my_task"` |
| `bind` | 绑定 self 参数 | `True` |
| `max_retries` | 最大重试次数 | `3` |
| `default_retry_delay` | 默认重试间隔（秒） | `30` |
| `soft_time_limit` | 软超时（触发异常） | `300` |
| `time_limit` | 硬超时（强制终止） | `360` |
| `autoretry_for` | 自动重试的异常类型 | `(ConnectionError,)` |
| `retry_backoff` | 指数退避重试 | `True` |
| `ignore_result` | 不存储结果 | `True` |

### 任务调用方式

```python
# 1. 异步调用（推荐）
task = my_task.delay(param1, param2)

# 2. 异步调用（完整参数）
task = my_task.apply_async(
    args=[param1, param2],
    countdown=10,        # 延迟10秒执行
    expires=3600,        # 任务过期时间
    queue="default",     # 指定队列
)

# 3. 同步调用（阻塞，仅用于测试）
result = my_task.apply(args=[param1, param2]).get()

# 4. 任务链（顺序执行）
from celery import chain
chain(task1.s(arg1), task2.s()).apply_async()

# 5. 任务组（并行执行）
from celery import group
group(task1.s(arg1), task2.s(arg2)).apply_async()
```

---

## 项目创建流程

```
用户输入自然语言需求
        ↓
┌───────────────────────────────────────┐
│  步骤1: 创建项目                        │
│  POST /api/v1/projects/               │
│  → 创建项目记录                         │
│  → 调度 Celery 任务生成 Schema + ER 图   │
│  ← 返回 project_id + task_id           │
└───────────────────────────────────────┘
        ↓
    [Celery Worker 执行]
    1. generate_schema_task (生成 Schema)
    2. generate_er_task (生成 ER 图)
        ↓
┌───────────────────────────────────────┐
│  步骤2: 用户确认/修改 Schema            │
│  POST /api/v1/projects/{id}/generate-ddl│
│  → 保存用户修改的 Schema                │
│  → 调度 Celery 任务生成 DDL             │
│  → 如 Schema 有变化，同时重新生成 ER 图  │
│  ← 返回 task_id                        │
└───────────────────────────────────────┘
        ↓
    [Celery Worker 执行]
    1. generate_ddl_task (生成 DDL)
    2. generate_er_task (可选，Schema 变化时)
        ↓
┌───────────────────────────────────────┐
│  步骤3: 用户确认/修改 DDL 并部署        │
│  POST /api/v1/projects/{id}/deploy     │
│  → 执行 DDL 建库建表                    │
│  → 项目状态变为 active                  │
│  ← 返回项目详情                         │
└───────────────────────────────────────┘
```

## Celery 任务定义

### 任务文件位置
`src/backend/app/tasks/ai_generation_tasks.py`

### 任务列表

| 任务名称 | 函数 | 描述 | 超时时间 |
|---------|------|------|---------|
| tasks.generate_schema | `generate_schema_task` | 生成 Schema | 300s |
| tasks.generate_er | `generate_er_task` | 生成 ER 图 | 60s |
| tasks.generate_ddl | `generate_ddl_task` | 生成 DDL | 150s |
| tasks.schema_er_pipeline | `schema_er_pipeline_task` | Schema + ER 流水线 | 600s |
| tasks.ddl_er_parallel | `ddl_er_parallel_task` | DDL + ER 并行任务 | 600s |

### 任务重试配置

- Schema 生成：最多重试 2 次，重试间隔 30 秒
- DDL 生成：最多重试 2 次，重试间隔 30 秒
- ER 图生成：最多重试 2 次，重试间隔 20 秒（失败不影响主流程）

## API 变更

### 新增接口

#### 查询任务状态
```
GET /api/v1/projects/tasks/{task_id}

Response:
{
    "code": 200,
    "message": "获取任务状态成功",
    "data": {
        "task_id": "abc123",
        "task_status": "SUCCESS",  // Celery 任务状态: PENDING, STARTED, SUCCESS, FAILURE, RETRY
        "ready": true,
        "successful": true,
        "result": {...},           // 任务执行结果
        "error": null,
        // 以下是项目业务状态（任务完成后返回）
        "project_id": 1,
        "creation_stage": "schema_generated",  // 项目创建阶段（业务状态）
        "project_status": "initializing"
    }
}
```

**两种状态说明：**

| 状态类型 | 字段 | 值 | 说明 |
|---------|------|------|------|
| Celery 任务状态 | `task_status` | `PENDING`, `STARTED`, `SUCCESS`, `FAILURE` | 异步任务执行状态 |
| 项目业务状态 | `creation_stage` | `generating_schema`, `schema_generated` 等 | 项目创建流程进度 |

前端应该：
1. 用 `task_status` 判断任务是否完成（`ready=true`）
2. 用 `creation_stage` 显示项目创建进度

#### 重新生成 ER 图
```
POST /api/v1/projects/{project_id}/regenerate-er

Request Body:
{
    "schema_text": "...",
    "ai_model": "gpt4"
}

Response:
{
    "code": 200,
    "message": "ER图重新生成请求已提交",
    "data": {
        "project_id": 1,
        "project_name": "...",
        "status": "...",
        "message": "正在重新生成 ER 图...",
        "task_id": "abc123"
    }
}
```

### 接口变更

#### 创建项目
- 移除 `BackgroundTasks` 依赖
- 响应中新增 `task_id` 字段

#### 生成 DDL
- 移除 `BackgroundTasks` 依赖
- 响应中新增 `task_id` 字段
- 自动检测 Schema 是否变化，决定是否重新生成 ER 图

## 启动 Celery Worker

```bash
# 在 src/backend/app 目录下执行
cd src/backend/app

# 启动 Worker
celery -A celery_app worker --loglevel=info

# 或指定并发数
celery -A celery_app worker --loglevel=info --concurrency=4
```

## 前端集成建议

### 方式一：轮询项目详情（推荐）

直接轮询项目详情接口获取 `creation_stage`，这是最简单的方式：

```javascript
async function pollProjectStatus(projectId) {
    const response = await fetch(`/api/v1/projects/${projectId}`);
    const data = await response.json();
    const stage = data.data.creation_stage;
    
    switch (stage) {
        case 'generating_schema':
            showLoading('正在生成 Schema...');
            setTimeout(() => pollProjectStatus(projectId), 2000);
            break;
        case 'schema_generated':
            // Schema 已生成，显示给用户确认
            showSchemaEditor(data.data.schema_definition?.schema);
            showERDiagram(data.data.er_diagram_code);
            break;
        case 'generating_ddl':
            showLoading('正在生成 DDL...');
            setTimeout(() => pollProjectStatus(projectId), 2000);
            break;
        case 'ddl_generated':
            // DDL 已生成，显示给用户确认
            showDDLEditor(data.data.ddl_statement);
            break;
        case 'completed':
            showSuccess('项目部署完成！');
            break;
        case 'schema_generation_failed':
        case 'ddl_generation_failed':
            showError('生成失败，请重试');
            break;
    }
}
```

### 方式二：轮询任务状态

使用返回的 `task_id` 轮询任务状态：

```javascript
async function pollTaskStatus(taskId) {
    const response = await fetch(`/api/v1/projects/tasks/${taskId}`);
    const data = await response.json();
    
    if (data.data.ready) {
        if (data.data.successful) {
            // 任务成功，根据 creation_stage 决定下一步
            const stage = data.data.creation_stage;
            handleStageChange(stage);
        } else {
            showError(data.data.error);
        }
    } else {
        setTimeout(() => pollTaskStatus(taskId), 2000);
    }
}
```

### 用户回访场景

用户离开后回来，直接调用项目详情接口即可获取之前的进度：

```javascript
// 用户回来时，直接获取项目详情
async function resumeProject(projectId) {
    const response = await fetch(`/api/v1/projects/${projectId}`);
    const data = await response.json();
    
    // 根据 creation_stage 恢复到对应步骤
    const stage = data.data.creation_stage;
    
    if (stage === 'schema_generated') {
        // 显示已生成的 Schema 和 ER 图，等待用户确认
        showSchemaEditor(data.data.schema_definition?.schema);
        showERDiagram(data.data.er_diagram_code);
    } else if (stage === 'ddl_generated') {
        // 显示已生成的 DDL，等待用户部署
        showDDLEditor(data.data.ddl_statement);
    }
    // ... 其他状态处理
}
```

## 项目状态枚举

| 状态值 | 说明 |
|-------|------|
| initializing | 正在初始化 |
| generating_schema | 正在生成 Schema |
| schema_generated | Schema 生成完毕，等待确认 |
| generating_ddl | 正在生成 DDL |
| ddl_generated | DDL 生成完毕，等待部署 |
| executing_ddl | 正在执行 DDL |
| completed | 部署完成 |
| schema_generation_failed | Schema 生成失败 |
| ddl_generation_failed | DDL 生成失败 |
