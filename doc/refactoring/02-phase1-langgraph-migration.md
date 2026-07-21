# 02 — Phase 1: Celery → LangGraph 编排层迁移

> **原则**：只换编排层，不修改 AI service 任何代码  
> **目标**：移除 Celery 依赖，用 LangGraph StateGraph 管理工作流  
> **改动范围**：编排层 + Service 层适配 + 配置清理

---

## 一、Step 0: 环境准备

### 1.1 安装依赖

```bash
pip uninstall celery  # 移除 Celery
pip install langgraph langgraph-checkpoint
```

更新 `requirements.txt`：

```
# 移除
# celery[redis]==5.3.4

# 新增
langgraph>=0.2.0
langgraph-checkpoint>=1.0.0
langgraph-checkpoint-postgres>=1.0.0  # 后续 Phase 3 使用
```

### 1.2 移除 Celery 相关代码

| 操作 | 文件 | 说明 |
|---|---|---|
| 删除 | `src/backend/app/celery_app.py` | Celery app 定义 |
| 修改 | `src/backend/app/tasks/__init__.py` | 移除 Celery task 导出 |
| 修改 | `docker-compose.yml` | 移除 `celery_worker` 服务定义 |
| 修改 | `src/.env` | 移除 `CELERY_BROKER_URL`、`CELERY_RESULT_BACKEND` 配置项 |
| 修改 | `src/backend/app/server.py` | 移除 Celery 相关的 lifespan 逻辑（如有） |

---

## 二、Step 0.5: 数据库会话管理方案

> **这是 Phase 1 中最重要的设计决策之一。** LangGraph node 如何获取 DB session，直接决定代码的正确性和性能。

### 2.1 三种场景对比

项目中有三种 DB 访问场景，各自的约束不同：

```
                     API 端点                Celery Worker           LangGraph Node
────────────────────────────────────────────────────────────────────────────────────
运行位置               FastAPI 进程内          独立操作系统进程          FastAPI 进程内

Engine 来源           app.state.psql_engine  每个 task 新建          复用 app.state
                      (进程启动时建，长期)    (用完 dispose)           (和 API 共享)

Session 获取方式      Depends(get_db)         PsqlHelper.get_session  PsqlHelper.get_session
                      由 FastAPI 注入         自己开                   自己开

Session 生命周期      跟随 HTTP 请求           跟随单个 task           跟随单个 node
                      请求结束→自动关闭        用完→自动关闭           用完→自动关闭

能否用 Depends        ✅ 能                   ❌ 不能                 ❌ 不能
                                               (没有 Request 对象)     (HTTP 请求已结束)

浪费程度               最优                   最大                    较小
                                             (反复建/拆连接池)        (只复用连接，不开新池)
```

**核心结论：** LangGraph node 和 Celery task 都无法使用 `Depends(get_db)`，因为它们都没有活跃的 HTTP 请求对象。但 LangGraph 的优势在于它**和 FastAPI 在同一个进程**，可以直接复用已初始化的 engine 连接池，不需要像 Celery 那样每次创建再 dispose 整个 engine。

### 2.2 比喻理解

```
Engine (连接池)  = 快递站（10 个快递员随时待命），进程启动时建好
Session          = 派工单（拿着它才能叫快递员干活），干完就交回
Connection       = 一次实际的 TCP 连接到数据库

API 请求：    客户进门 → 前台给派工单 → 办事 → 客户走了，派工单收回
              快递站一直在，不重建

Celery：      隔壁办公楼的外包团队 → 看不到我们快递站
              只能自己临时搭一个 → 干活 → 拆掉 → 下次再搭

LangGraph：   同一栋楼的后台办公室 → 能看见同一个快递站
              自己拿张新派工单干活 → 干完交回派工单 → 快递站不拆
```

### 2.3 实现方案

在 `app/graphs/` 下新建 `db.py`，**直接复用 FastAPI 进程的 engine**（`server.py:170` 暴露的 `my_app` 模块级变量）：

```python
# app/graphs/db.py
"""Graph 节点使用的数据库会话工具 —— 直接复用 FastAPI 进程的 engine"""

from server import my_app
from core.database import PsqlHelper
from sqlalchemy.ext.asyncio import AsyncEngine


def _get_shared_engine() -> AsyncEngine:
    """
    获取 FastAPI 进程共享的 engine（懒加载，不新建连接池）。
    
    为什么可以直接 import my_app：
    - server.py 第 170 行 `my_app = create_app()` 是模块级变量
    - app.state.psql_engine 在 lifespan startup 时初始化 (server.py:59)
    - graph node 运行时 startup 早已完成，engine 一定存在
    - graphs/ → server.py 没有循环导入风险（server.py 不 import graphs/）
    """
    engine = my_app.state.psql_engine
    if engine is None:
        raise RuntimeError("psql_engine 尚未初始化，startup 可能未完成")
    return engine


def _get_session():
    """便捷方法：直接从共享 engine 获取一个 session"""
    return PsqlHelper.get_session(_get_shared_engine())
```

**为什么这比新建 engine 更好？**

| | 新建 `PsqlHelper._get_async_engine(config.db)` | 直接用 `my_app.state.psql_engine` |
|---|---|---|
| 连接池数量 | 再建一个，两个池各占连接 | **同一个池**，不浪费 |
| 生命周期 | 需自行管理 dispose 时机 | 跟 FastAPI 走，`close_services` 统一关 |
| 配置一致性 | 两个入口读 `config.db`，可能不同步 | **单一来源**，绝对一致 |
| 代码量 | 需要 `global _engine` + 懒加载 + dispose 管理 | 三行代码 |

每个 graph node 使用时：

```python
# 在 node 函数中使用
from graphs.db import _get_session

async def some_node(state: ProjectState) -> dict:
    async with _get_session() as db:
        # 使用 db 进行 CRUD 操作
        ...
    # async with 退出时自动 commit/rollback/close session
    # engine 不动，连接归还到池
```

**对比三种方式的完整代码：**

```python
# ──── Celery（旧）—— 每次建 engine + dispose ────
async def _update_project_field(project_id: int, **update_fields) -> bool:
    temp_engine = PsqlHelper._get_async_engine(config.db)  # 建新快递站
    try:
        async with PsqlHelper.get_session(temp_engine) as session:
            ...
    finally:
        await temp_engine.dispose()  # 拆掉快递站

# ──── 文档初版 —— 模块级新建 engine（多此一举）────
_engine: AsyncEngine = None

def _get_shared_engine():
    global _engine
    if _engine is None:
        _engine = PsqlHelper._get_async_engine(config.db)  # 又建一个快递站
    return _engine

# ──── 最终方案 —— 直接用 FastAPI 的 engine（最优）────
from server import my_app

def _get_shared_engine():
    return my_app.state.psql_engine   # 就是同一个快递站，零额外开销
```

> **时序安全说明：** Graph node 只在 `asyncio.create_task(_run_graph(...))` 时执行，此时 FastAPI 的 lifespan startup 早已完成，`my_app.state.psql_engine` 一定存在。不存在"import 时 engine 还未初始化"的问题，因为 `_get_shared_engine()` 是函数调用时才解析，不是 import 时解析。

---

## 三、Step 1: 定义 Graph State

创建 `src/backend/app/graphs/state.py`：

```python
from typing import TypedDict, Optional, Annotated
from datetime import datetime
from operator import add


class ProjectState(TypedDict, total=False):
    """LangGraph 全局状态 —— 替代原有的 DB creation_stage + 函数参数传递"""

    # ──── 输入参数 ────
    project_id: int
    db_type: str                 # mysql / postgresql / sqlite
    db_name: str
    requirements: str            # 用户需求描述
    ai_model: str                # gpt4 / chatgpt / qwen / deepseek

    # ──── 各步骤产出 ────
    schema_text: Optional[str]   # generate_schema 产出
    er_diagram_code: Optional[str]   # generate_er 产出
    ddl_statement: Optional[str]     # generate_ddl 产出

    # ──── 流程控制 ────
    current_stage: str           # 替代 creation_stage
    error_message: Optional[str]
    regenerate_er: bool          # DDL 流程中是否重新生成 ER

    # ──── 时间戳 ────
    started_at: Optional[str]
    completed_at: Optional[str]

    # ──── 累积信息（用于调试/日志）───
    node_history: Annotated[list[str], add]
```

### 2.2 State 与现有 creation_stage 对照

| creation_stage | ProjectState.current_stage | 触发节点 |
|---|---|---|
| `generating_schema` | `generating_schema` | `generate_schema` 节点开始 |
| `schema_generated` | `schema_generated` | `generate_schema` 节点成功结束 |
| `generating_ddl` | `generating_ddl` | `generate_ddl` 节点开始 |
| `ddl_generated` | `ddl_generated` | `generate_ddl` 节点成功结束 |
| `completed` | `completed` | 最终节点结束 |

---

## 三、Step 2: 实现 Graph 节点

### 3.1 目录结构

```
src/backend/app/graphs/
├── __init__.py
├── db.py                     # 共享 engine + session 工具
├── state.py
├── schema_er_graph.py        # Schema → ER 流程
├── ddl_er_graph.py           # DDL → ER 流程
└── nodes/
    ├── __init__.py
    ├── schema_node.py        # generate_schema 节点
    ├── er_node.py            # generate_er 节点
    └── ddl_node.py           # generate_ddl 节点
```

### 3.2 schema_node.py

```python
"""Schema 生成节点 —— 替代 generate_schema_task"""

from core.config import config
from core.database import PsqlHelper
from core.log import log
from crud.crud_project import crud_project
from schema import project as schemas
from graphs.db import _get_shared_engine
from graphs.state import ProjectState
from service.ai_service import AIService
from redis_client.cache_service import cache_service
from redis_client.redis_keys import redis_key_manager
import logging

logger = logging.getLogger(__name__)


async def generate_schema_node(state: ProjectState) -> dict:
    """调用 AI 生成 schema，更新 DB，返回新 state"""
    project_id = state["project_id"]
    engine = _get_shared_engine()

    try:
        # 1. 更新 DB 状态：creation_stage → generating_schema
        async with PsqlHelper.get_session(engine) as db:
            await crud_project.update(
                db, project_id,
                creation_stage=schemas.CreationStageEnum.GENERATING_SCHEMA.value
            )

        # 2. 调用 AI service（Phase 1 保持不变）
        schema_text = await AIService.generate_schema(
            requirements=state["requirements"],
            db_type=state["db_type"],
            db_name=state["db_name"],
            ai_model=state["ai_model"],
        )

        if not schema_text or "error" in schema_text.lower():
            logger.error(f"Schema generation failed for project {project_id}")
            # 更新失败状态
            async with PsqlHelper.get_session(engine) as db:
                await crud_project.update(
                    db, project_id, creation_stage="failed"
                )
            return {
                "error_message": f"Schema generation failed: {schema_text}",
                "current_stage": "failed",
                "node_history": ["generate_schema"],
            }

        # 3. 保存 Schema 结果
        async with PsqlHelper.get_session(engine) as db:
            # 获取当前项目
            project = await crud_project.get(db, project_id)
            if project:
                current_def = project.schema_definition or {}
                current_def['schema'] = schema_text
                current_def['generated_db_name'] = state["db_name"]

                await crud_project.update(
                    db, project_id,
                    schema_definition=current_def,
                    creation_stage=schemas.CreationStageEnum.SCHEMA_GENERATED.value
                )

        # 4. 清理 Redis 缓存
        async with PsqlHelper.get_session(engine) as db:
            project = await crud_project.get(db, project_id)
            if project:
                project_key = redis_key_manager.get_project_info_key(project_id)
                await cache_service.delete(project_key)
                if project.user_id:
                    user_projects_pattern = redis_key_manager.get_user_projects_key(
                        project.user_id
                    )
                    await cache_service.delete_pattern(user_projects_pattern)

        log.info(f"Schema generated for project {project_id}")
        logger.info(f"[Graph] Schema generated for project {project_id}")
        return {
            "schema_text": schema_text,
            "current_stage": "schema_generated",
            "node_history": ["generate_schema"],
        }

    except Exception as e:
        logger.exception(f"Schema generation error for project {project_id}")
        async with PsqlHelper.get_session(engine) as db:
            await crud_project.update(
                db, project_id, creation_stage="failed"
            )
        return {
            "error_message": str(e),
            "current_stage": "failed",
            "node_history": ["generate_schema"],
        }
```

### 3.3 er_node.py

```python
"""ER 图生成节点 —— 替代 generate_er_task"""

from core.config import config
from core.database import PsqlHelper
from core.log import log
from crud.crud_project import crud_project
from graphs.db import _get_shared_engine
from graphs.state import ProjectState
from service.ai_service import AIService
from redis_client.cache_service import cache_service
from redis_client.redis_keys import redis_key_manager
import logging

logger = logging.getLogger(__name__)


async def generate_er_node(state: ProjectState) -> dict:
    """调用 AI 生成 Mermaid ER 图"""
    project_id = state["project_id"]
    schema_text = state.get("schema_text", "")
    engine = _get_shared_engine()

    try:
        er_code = await AIService.generate_mermaid_code(
            schema_text=schema_text,
            ai_model=state["ai_model"],
        )

        async with PsqlHelper.get_session(engine) as db:
            await crud_project.update(
                db, project_id, er_diagram_code=er_code
            )

        # 清理缓存
        async with PsqlHelper.get_session(engine) as db:
            project = await crud_project.get(db, project_id)
            if project:
                project_key = redis_key_manager.get_project_info_key(project_id)
                await cache_service.delete(project_key)

        logger.info(f"ER diagram generated for project {project_id}")
        return {
            "er_diagram_code": er_code,
            "node_history": ["generate_er"],
        }

    except Exception as e:
        # ER 是非关键步骤，失败不阻断流程
        logger.warning(f"ER generation failed (non-critical): {e}")
        return {
            "er_diagram_code": None,
            "node_history": ["generate_er"],
        }
```

### 3.4 ddl_node.py

```python
"""DDL 生成节点 —— 替代 generate_ddl_task"""

from core.config import config
from core.database import PsqlHelper
from core.log import log
from crud.crud_project import crud_project
from schema import project as schemas
from graphs.db import _get_shared_engine
from graphs.state import ProjectState
from service.ai_service import AIService
from redis_client.cache_service import cache_service
from redis_client.redis_keys import redis_key_manager
import logging

logger = logging.getLogger(__name__)


async def generate_ddl_node(state: ProjectState) -> dict:
    """调用 AI 生成 DDL 语句"""
    project_id = state["project_id"]
    schema_text = state.get("schema_text", "")
    engine = _get_shared_engine()

    try:
        # 1. 更新阶段状态
        async with PsqlHelper.get_session(engine) as db:
            await crud_project.update(
                db, project_id,
                creation_stage=schemas.CreationStageEnum.GENERATING_DDL.value
            )

        # 2. 调用 AI 生成 DDL
        ddl = await AIService.generate_ddl(
            schema_text=schema_text,
            requirements=state["requirements"],
            db_type=state["db_type"],
            db_name=state["db_name"],
            ai_model=state["ai_model"],
        )

        if not ddl or "error" in ddl.lower():
            logger.error(f"DDL generation failed for project {project_id}")
            async with PsqlHelper.get_session(engine) as db:
                await crud_project.update(db, project_id, creation_stage="failed")
            return {
                "error_message": f"DDL generation failed: {ddl}",
                "current_stage": "failed",
                "node_history": ["generate_ddl"],
            }

        # 3. 保存 DDL
        async with PsqlHelper.get_session(engine) as db:
            await crud_project.update(
                db, project_id,
                ddl_statement=ddl,
                creation_stage=schemas.CreationStageEnum.DDL_GENERATED.value,
                project_status="pending_confirmation",
            )

        # 4. 清理 Redis 缓存
        async with PsqlHelper.get_session(engine) as db:
            project = await crud_project.get(db, project_id)
            if project:
                project_key = redis_key_manager.get_project_info_key(project_id)
                await cache_service.delete(project_key)
                if project.user_id:
                    user_projects_pattern = redis_key_manager.get_user_projects_key(
                        project.user_id
                    )
                    await cache_service.delete_pattern(user_projects_pattern)

        log.info(f"DDL generated for project {project_id}")
        logger.info(f"[Graph] DDL generated for project {project_id}")
        return {
            "ddl_statement": ddl,
            "current_stage": "ddl_generated",
            "node_history": ["generate_ddl"],
        }

    except Exception as e:
        logger.exception(f"DDL generation error for project {project_id}")
        async with PsqlHelper.get_session(engine) as db:
            await crud_project.update(db, project_id, creation_stage="failed")
        return {
            "error_message": str(e),
            "current_stage": "failed",
            "node_history": ["generate_ddl"],
        }
```

---

## 四、Step 3: 组装 Graph

### 4.1 schema_er_graph.py

```python
"""Schema + ER 流水线 —— 替代 schema_er_pipeline_task"""

from langgraph.graph import StateGraph, START, END
from graphs.state import ProjectState
from graphs.nodes.schema_node import generate_schema_node
from graphs.nodes.er_node import generate_er_node


def route_after_schema(state: ProjectState) -> str:
    """Schema 生成后的条件路由"""
    if state.get("error_message"):
        return "failed"
    return "success"


# ═══════════════════════════════════════════
# 构建 Graph
# ═══════════════════════════════════════════
builder = StateGraph(ProjectState)

builder.add_node("generate_schema", generate_schema_node)
builder.add_node("generate_er", generate_er_node)

builder.add_edge(START, "generate_schema")

builder.add_conditional_edges(
    "generate_schema",
    route_after_schema,
    {
        "success": "generate_er",
        "failed": END,
    }
)

builder.add_edge("generate_er", END)

schema_er_graph = builder.compile()
```

### 4.2 ddl_er_graph.py

```python
"""DDL + (可选) ER 流水线 —— 替代 ddl_er_parallel_task"""

from langgraph.graph import StateGraph, START, END
from graphs.state import ProjectState
from graphs.nodes.ddl_node import generate_ddl_node
from graphs.nodes.er_node import generate_er_node


def route_after_ddl(state: ProjectState) -> str:
    """DDL 生成后的条件路由"""
    if state.get("error_message"):
        return "failed"
    if state.get("regenerate_er") and state.get("schema_text"):
        return "regenerate_er"
    return "done"


def route_after_er(state: ProjectState) -> str:
    """ER 生成后直接结束（非关键路径）"""
    return "done"


# ═══════════════════════════════════════════
# 构建 Graph
# ═══════════════════════════════════════════
builder = StateGraph(ProjectState)

builder.add_node("generate_ddl", generate_ddl_node)
builder.add_node("regenerate_er", generate_er_node)

builder.add_edge(START, "generate_ddl")

builder.add_conditional_edges(
    "generate_ddl",
    route_after_ddl,
    {
        "done": END,
        "failed": END,
        "regenerate_er": "regenerate_er",
    }
)

builder.add_conditional_edges(
    "regenerate_er",
    route_after_er,
    {"done": END}
)

ddl_er_graph = builder.compile()
```

---

## 五、Step 4: Service 层适配

### 5.1 改动 project_service.py

**原代码模式：**

```python
# 原：Celery .delay() 调用
def _dispatch_schema_er_task(project_id, requirements, db_name, db_type, ai_model) -> str:
    task = schema_er_pipeline_task.delay(
        project_id=project_id,
        requirements=requirements,
        db_name=db_name,
        db_type=db_type,
        ai_model=ai_model,
    )
    return task.id
```

**改为 LangGraph 调用：**

```python
import asyncio
import uuid
from graphs.schema_er_graph import schema_er_graph
from graphs.ddl_er_graph import ddl_er_graph
from graphs.state import ProjectState

# 内存中的运行任务跟踪（替代 Celery task_id 查询）
_running_tasks: dict[str, dict] = {}


def _dispatch_schema_er_task(
    project_id: int,
    requirements: str,
    db_name: str,
    db_type: str,
    ai_model: str,
) -> str:
    """
    触发 Schema + ER 流水线（异步，立即返回 task_id）
    替代 schema_er_pipeline_task.delay()
    """
    task_id = str(uuid.uuid4())
    _running_tasks[task_id] = {"status": "PENDING", "project_id": project_id}

    state: ProjectState = {
        "project_id": project_id,
        "requirements": requirements,
        "db_name": db_name,
        "db_type": db_type,
        "ai_model": ai_model,
        "current_stage": "generating_schema",
        "regenerate_er": False,
        "node_history": [],
    }

    # 异步启动 graph 执行，不阻塞 HTTP 响应
    asyncio.create_task(_run_graph(task_id, schema_er_graph, state))
    return task_id


def _dispatch_ddl_er_task(
    project_id: int,
    schema_text: str,
    requirements: str,
    db_type: str,
    db_name: str,
    ai_model: str,
    regenerate_er: bool,
) -> str:
    """触发 DDL + (可选) ER 流水线"""
    task_id = str(uuid.uuid4())
    _running_tasks[task_id] = {"status": "PENDING", "project_id": project_id}

    state: ProjectState = {
        "project_id": project_id,
        "schema_text": schema_text,
        "requirements": requirements,
        "db_type": db_type,
        "db_name": db_name,
        "ai_model": ai_model,
        "regenerate_er": regenerate_er,
        "current_stage": "generating_ddl",
        "node_history": [],
    }

    asyncio.create_task(_run_graph(task_id, ddl_er_graph, state))
    return task_id


def _dispatch_er_only_task(project_id: int, schema_text: str, ai_model: str) -> str:
    """单独触发 ER 生成（当前没有独立 graph，直接用 er node）"""
    task_id = str(uuid.uuid4())
    _running_tasks[task_id] = {"status": "PENDING", "project_id": project_id}

    from graphs.nodes.er_node import generate_er_node

    state: ProjectState = {
        "project_id": project_id,
        "schema_text": schema_text,
        "ai_model": ai_model,
        "current_stage": "generating_er",
        "node_history": [],
    }

    async def _run_er_node():
        try:
            result = await generate_er_node(state)
            _running_tasks[task_id] = {
                "status": "FAILURE" if result.get("error_message") else "SUCCESS",
                "project_id": project_id,
                "result": result,
            }
        except Exception as e:
            _running_tasks[task_id] = {"status": "FAILURE", "project_id": project_id, "error": str(e)}

    asyncio.create_task(_run_er_node())
    return task_id


async def _run_graph(task_id: str, graph, state: ProjectState):
    """后台执行 LangGraph graph，更新任务状态"""
    try:
        result = await graph.ainvoke(state)
        _running_tasks[task_id] = {
            "status": "FAILURE" if result.get("error_message") else "SUCCESS",
            "project_id": state["project_id"],
            "result": result,
        }
    except Exception as e:
        _running_tasks[task_id] = {"status": "FAILURE", "project_id": state["project_id"], "error": str(e)}


def get_graph_task_status(task_id: str) -> dict:
    """查询 graph 任务状态 —— 替代原有的 Celery AsyncResult 查询"""
    return _running_tasks.get(task_id, {"status": "NOT_FOUND"})
```

### 5.2 模型选择解耦 —— 解除 ai_model 硬编码 ✅ 已完成

> **已修复的问题：** `project_service.py:369` 原本 `pop` 掉用户传的 `ai_model` 然后硬编码 `ai_model = "gpt4"`。DDL 生成（`project_service.py:465`）和 ER 重生成（`project_service.py:792`）同样硬编码。用户在前端选了模型会被后端忽略。
> 
> **修改后：** 用户传的 `ai_model` 真正生效，三层 fallback 兜底。

#### 改动文件

| 文件 | 改动内容 |
|---|---|
| `schema/project.py:70` | `ProjectCreate.ai_model`: `Literal["gpt4","deepseek","chatgpt"]` → `Optional[str] = None` |
| `schema/project.py:124` | `GenerateDDLRequest` 新增 `ai_model: Optional[str] = None` 字段 |
| `schema/project.py:132` | `RegenerateERRequest.ai_model`: `Literal[...]` → `Optional[str] = None` |
| `core/llm.py:12-15` | 新增 `TASK_DEFAULT_MODEL` 字典（任务→默认模型映射，可配置） |
| `core/llm.py:135-146` | 新增 `resolve_model_name()` 工具函数（三层 fallback） |
| `core/llm.py:125-132` | 修复 `get_model_for_task()` — 移除不存在的 `app_config` 引用 |
| `service/project_service.py:24` | import 新增 `TASK_DEFAULT_MODEL` |
| `service/project_service.py:369-374` | `create_project_service`: 移除 `pop` + 硬编码 → `project_data.get('ai_model') or model_registry.get_default_name()` |
| `service/project_service.py:434-443` | `request_ddl_generation_service`: 移除 `ai_model="gpt4"` → 读 `data.ai_model` + fallback |
| `service/project_service.py:218` | `_dispatch_ddl_er_task`: 移除参数默认值 `"gpt4"` |
| `service/project_service.py:798` | `regenerate_project_er_service`: 移除 `ai_model="gpt4"` 默认 → fallback 逻辑 |
| `service/project_service.py:246-263` | 删除旧 Celery 版 `_dispatch_er_only_task`（被新 graph 版覆盖的死代码） |

#### 三层 fallback 机制

```
用户前端传了 ai_model  →  直接使用用户选择           (优先级最高)
前端没传               →  读 TASK_DEFAULT_MODEL 默认值 (系统推荐)
代码也没配默认          →  注册表第一个模型            (兜底)
```

后端 API 接口行为：

| 端点 | 改前 | 改后 |
|---|---|---|
| `POST /projects/` | 前端传 `ai_model` 被 `pop` 丢弃，强制 `"gpt4"` | 前端传了就生效，不传走 fallback |
| `POST /{id}/generate-ddl` | `GenerateDDLRequest` 无 `ai_model` 字段，硬编码 `"gpt4"` | 新增 `ai_model` 可选字段，前端可选模型 |
| `POST /{id}/regenerate-er` | `RegenerateERRequest.ai_model` 有默认值 `"gpt4"` | 改为 `Optional[str] = None`，走 fallback |

### 5.3 前端任务状态端点适配

```python
# app/api/v1/projects.py 中适配

@router.get("/projects/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    查询任务状态 —— 兼容原有 GET /projects/tasks/{task_id} 接口
    原先调用 Celery AsyncResult，现在改为查内存 _running_tasks
    """
    from service.project_service import get_graph_task_status

    task_info = get_graph_task_status(task_id)
    # 保持和原来相同的响应格式
    return {
        "task_id": task_id,
        "status": task_info["status"],
        "project_id": task_info.get("project_id"),
        "info": task_info.get("result") or task_info.get("error"),
    }
```

---

## 六、Step 5: 清理工作

### 6.1 docker-compose.yml 改动

移除 `celery_worker` 服务：

```yaml
# 删除整个 celery_worker 服务块：
# celery_worker:
#   build:
#     context: ./src/backend
#     dockerfile: Dockerfile.dev
#   command: celery -A celery_app worker --loglevel=info -Q celery,default,ai_tasks
#   depends_on:
#     - redis
#     - backend
#   environment: ...
#   volumes: ...
```

### 6.2 环境变量清理

`.env` 中移除：

```
# 删除以下行
CELERY_BROKER_URL=redis://...
CELERY_RESULT_BACKEND=redis://...
```

### 6.3 删除文件清单

```
删除: src/backend/app/celery_app.py
归档: src/backend/app/tasks/ai_generation_tasks.py  (保留为参考，功能移入 graphs/)
```

---

## 七、验证 Checklist

Phase 1 完成后，逐项验证：

- [ ] `pip install` 不报错（celery 已移除，langgraph 已安装）
- [ ] FastAPI 启动成功（`uvicorn server:my_app`）
- [ ] **不需要** 单独的 Celery worker 进程
- [ ] `POST /api/v1/projects/` 创建项目，返回 task_id
- [ ] `GET /api/v1/projects/tasks/{task_id}` 轮询能查到状态变化
- [ ] Schema 生成成功，DB 中 `creation_stage` 更新为 `schema_generated`
- [ ] ER 图生成成功（或非关键失败不阻塞流程）
- [ ] `POST /api/v1/projects/{id}/generate-ddl` → DDL 生成成功
- [ ] `POST /api/v1/projects/{id}/deploy` → 部署成功（此步未改动，仍应正常）
- [ ] Docker Compose 启动不再报 celery_worker 缺失
- [ ] 原有单元测试通过（或适配后通过）
- [ ] 前端传 `ai_model: "deepseek"` → 后端不再被硬编码覆盖 → 实际使用 deepseek 模型
- [ ] 前端不传 `ai_model` → 走 `config.yaml → tasks` 默认配置 → 兜底到注册表默认模型

---

## 八、常见问题

**Q: asyncio.create_task 是否可靠？进程重启任务丢失怎么办？**

A: Phase 1 阶段用内存管理任务状态，接受进程重启后正在执行的任务丢失（和原 Celery 行为类似）。Phase 3 引入 LangGraph checkpoint 持久化后可解决。

**Q: 为什么不用 Celery chain/canvas API 替代手动编排？**

A: 原代码没有用 Celery chain（而是手动 sequential 调用），说明编排逻辑本身不适合简单的链式表达。LangGraph 的条件边和状态管理更适合。

**Q: 为什么 graph node 不能直接用 API 层的 `Depends(get_db)` 注入 session？**

A: `Depends(get_db)` 注入的 session 生命周期绑定到 HTTP 请求。LangGraph graph 通过 `asyncio.create_task()` 在后台异步执行，此时 HTTP 请求早已结束、session 已关闭。正确做法是复用进程级 engine 连接池（`_get_shared_engine()`），每个 node 独立创建 session（`PsqlHelper.get_session(engine)`），session 用完即关但 engine 不 dispose。详见 Step 0.5 的对照表。
