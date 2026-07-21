# 05 — 前端接口兼容方案

> **原则**：Phase 1 完全保持 API 接口签名不变  
> **Phase 3 后增加**：Human-in-the-Loop /confirm 端点、未来 SSE 流式推送升级  

---

## 一、现有前端依赖的 API

| 方法 | 路径 | 用途 | Phase 1 影响 |
|---|---|---|---|
| POST | `/api/v1/projects/` | 创建项目，触发 schema 生成 | 返回值不变 `{project_id, task_id}` |
| GET | `/api/v1/projects/tasks/{task_id}` | 轮询 Celery task 状态 | 不变 |
| POST | `/api/v1/projects/{id}/generate-ddl` | 确认 schema，触发 DDL 生成 | 返回值不变 `{project_id, task_id}` |
| POST | `/api/v1/projects/{id}/deploy` | 确认 DDL，触发部署 | 不变（同步执行，不涉及编排层） |
| POST | `/api/v1/projects/{id}/regenerate-er` | 重新生成 ER 图 | 返回值不变 `{task_id}` |
| GET | `/api/v1/projects/{id}` | 获取项目详情（含 creation_stage） | 不变 |
| GET | `/api/v1/projects/` | 获取用户项目列表 | 不变 |

---

## 二、Phase 1 兼容保证

### 2.1 task_id 格式兼容

原先 Celery 的 `task_id` 是 UUID 格式，LangGraph 中我们继续用 `uuid.uuid4()` 生成，前端无需改动。

### 2.2 任务状态查询兼容

原先 `GET /projects/tasks/{task_id}` 返回：

```json
{
    "task_id": "abc-123",
    "status": "SUCCESS",
    "project_id": 42,
    "info": {...}
}
```

Phase 1 的 `get_graph_task_status()` 返回：

```json
{
    "task_id": "abc-123",
    "status": "SUCCESS",       // PENDING / RUNNING / SUCCESS / FAILURE
    "project_id": 42,
    "info": {"current_stage": "schema_generated", ...}
}
```

前端状态判断逻辑保持不变。

### 2.3 creation_stage 兼容

各阶段 creation_stage 值保持不变：

```
initializing → generating_schema → schema_generated
                                   → generating_ddl
                                   → ddl_generated
                                   → executing_ddl
                                   → completed
```

前端根据 `creation_stage` 展示不同 UI 状态的逻辑完全兼容。

---

## 三、Phase 3 新增接口

### 3.1 Human-in-the-Loop 确认

```
POST /api/v1/projects/{project_id}/confirm
Body: { "action": "approve" | "reject" }
Response: { "project_id": 42, "status": "approved", "next_stage": "generating_ddl" }
```

此接口是 Phase 3 新增的，前端需要新增对应的确认按钮逻辑。但这可以在你学习前端之后再做。

### 3.2 Graph 状态查询（增强版）

```
GET /api/v1/projects/{project_id}/graph-state
Response: {
    "project_id": 42,
    "current_stage": "generating_ddl",
    "agent_status": "ddl_agent_running",
    "node_history": ["schema_agent", "human_confirm"],
    "checkpoint_id": "1ef-..."
}
```

---

## 四、Phase 3 引入的 SSE 流式推送方案（前瞻）

当需要实时推送进度时，将轮询替换为 SSE：

```python
# app/api/v1/projects.py

from fastapi.responses import StreamingResponse
import json


@router.get("/projects/{project_id}/stream")
async def stream_project_progress(project_id: int):
    """SSE 流式推送项目进度"""
    async def event_generator():
        checkpointer = get_checkpointer()
        config = {"configurable": {"thread_id": str(project_id)}}
        graph = build_supervisor_graph(checkpointer=checkpointer)

        async for event in graph.astream(None, config=config):
            yield f"data: {json.dumps(event)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

**前端接入方式**（供后续学习前端时参考）：

```typescript
// 前端 EventSource 监听
const eventSource = new EventSource(`/api/v1/projects/${projectId}/stream`);

eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
        eventSource.close();
        return;
    }
    const data = JSON.parse(event.data);
    updateUI(data);
};
```

---

## 五、改动影响矩阵

| API 端点 | Phase 1 | Phase 2 | Phase 3 |
|---|---|---|---|
| POST `/projects/` | 返回值不变 | 不变 | 不变 |
| GET `/projects/tasks/{task_id}` | 返回值格式不变 | 不变 | 可能改为返回更丰富的 graph 状态 |
| POST `/projects/{id}/generate-ddl` | 返回值不变 | 不变 | 不变 |
| POST `/projects/{id}/deploy` | 不变 | 不变 | 可能改为 Agent 异步执行 |
| POST `/projects/{id}/regenerate-er` | 返回值不变 | 不变 | 不变 |
| GET `/projects/{id}` | 不变 | 不变 | 可能增加 `agent_log` 字段 |
| GET `/projects/` | 不变 | 不变 | 不变 |
| POST `/projects/{id}/confirm` | — | — | **新增** |
| GET `/projects/{id}/stream` | — | — | **新增** (SSE) |

---

## 六、总结

1. **Phase 1 和 Phase 2 期间**：前端代码**完全不需要改动**。所有的编排层变化对前端透明。
2. **Phase 3 期间**：新增 `/confirm` 端点用于 Human-in-the-Loop 确认，但旧的项目创建和 DDL 生成流程仍然兼容。前端可以逐步适配。
3. **SSE 流式推送**是可选升级，不影响现有功能。可以在你学习前端之后再做。
