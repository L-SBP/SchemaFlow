# SchemaFlow 重构方案索引

> 重构人：单人  
> 重构范围：后端多智能体编排层 Celery → LangGraph  
> 原始项目：3班-葫芦娃救bug 小组项目

---

## 重构背景

SchemaFlow 当前使用 **Celery + Redis** 实现异步任务编排，通过 5 个 Celery Task 串联完成 Schema 生成 → ER 图生成 → DDL 生成 → 部署的流水线。该架构存在以下问题：

1. **编排逻辑分散**：Orchestrator Task 中手写 try/except + 逐任务调用，难以维护和扩展
2. **外部 AI 服务耦合**：依赖 3 个独立部署的外部 AI 微服务，稳定性不可控
3. **不具备 Agent 能力**：当前是固定的 Task Pipeline，无法实现 LLM Agent 的自主推理、工具调用、多轮协商

**目标**：分 3 个阶段，将项目从 Celery 任务流水线逐步演进为 LangGraph 多智能体编排系统。

---

## 阶段路线图

```
Phase 1                    Phase 2                    Phase 3
Celery → LangGraph         外部API → LangChain         Task → LLM Agent
[编排层替换]        ──→     [AI后端统一]       ──→     [Agent化改造]
                                                                    
改动范围：                 改动范围：                  改动范围：
  app/tasks/  重写            app/service/ai_service.py   app/graphs/nodes/
  app/celery_app.py 删除      app/core/prompts/ 新建      app/tools/ 新建
  app/service/project_service.py 适配                      checkpoint 持久化
  app/graphs/ 新建
```

---

## 技术栈变更

| 组件 | 当前 | 目标 (Phase 1) | 目标 (Phase 2+) |
|---|---|---|---|
| 任务编排 | Celery 5.3.4 | LangGraph | LangGraph |
| 消息代理 | Redis | 无需 (asyncio) | 无需 |
| 状态管理 | PostgreSQL + Redis | LangGraph State + Checkpoint | LangGraph Checkpoint |
| Schema 生成 | Gradio API (外部) | 不变 | LangChain ChatModel |
| DDL 生成 | schema2ddl.fun (外部) | 不变 | LangChain ChatModel |
| ER 生成 | OpenAI 兼容 API (外部) | 不变 | 统一 LLM 工厂 |
| 前端通信 | HTTP 轮询 task_id | 不变 | 不变 (后续改 SSE) |

---

## 文档索引

| 文档 | 说明 |
|---|---|
| [01-重构总览](./01-refactoring-overview.md) | 现状分析、目标架构、新旧对比 |
| [02-Phase1-LangGraph 编排层迁移](./02-phase1-langgraph-migration.md) | Celery → LangGraph 详细实施方案 |
| [03-Phase2-AI 后端统一](./03-phase2-ai-backend-unification.md) | 外部 API → LangChain 统一 |
| [04-Phase3-Agent 化改造](./04-phase3-agent-transformation.md) | Task → LLM Agent 多智能体 |
| [05-前端接口兼容方案](./05-api-compatibility.md) | API 兼容、未来 SSE 升级路线 |

---

## 改造范围文件清单

### Phase 1 涉及文件

| 操作 | 文件路径 |
|---|---|
| **重写** | `src/backend/app/tasks/ai_generation_tasks.py` |
| **删除** | `src/backend/app/celery_app.py` |
| **修改** | `src/backend/app/service/project_service.py` |
| **修改** | `src/backend/app/api/v1/projects.py` (task 状态端点) |
| **修改** | `src/backend/requirements.txt` |
| **修改** | `src/.env` |
| **修改** | `docker-compose.yml` |
| **新建** | `src/backend/app/graphs/__init__.py` |
| **新建** | `src/backend/app/graphs/db.py` |
| **新建** | `src/backend/app/graphs/state.py` |
| **新建** | `src/backend/app/graphs/schema_er_graph.py` |
| **新建** | `src/backend/app/graphs/ddl_er_graph.py` |
| **新建** | `src/backend/app/graphs/nodes/__init__.py` |
| **新建** | `src/backend/app/graphs/nodes/schema_node.py` |
| **新建** | `src/backend/app/graphs/nodes/er_node.py` |
| **新建** | `src/backend/app/graphs/nodes/ddl_node.py` |

### Phase 2 涉及文件

| 操作 | 文件路径 |
|---|---|
| **重写** | `src/backend/app/service/ai_service.py` |
| **新建** | `src/backend/app/core/llm.py` |
| **新建** | `src/backend/app/core/seed_ai_models.py` |
| **新建** | `src/backend/app/core/prompts/__init__.py` |
| **新建** | `src/backend/app/core/prompts/schema_prompt.py` |
| **新建** | `src/backend/app/core/prompts/ddl_prompt.py` |
| **新建** | `src/backend/app/core/prompts/er_prompt.py` |
| **修改** | `src/backend/app/models/ai_model_config.py` (新增 provider, is_preset 字段) |
| **修改** | `src/backend/app/schema/ai_model_config.py` |
| **修改** | `src/backend/app/api/v1/endpoints/admin.py` |
| **修改** | `src/backend/app/server.py` |
| **修改** | `src/backend/app/service/chat_service.py` (移除 FALLBACK_MODEL_REGISTRY) |
| **修改** | `src/backend/config.yaml` (新增 tasks 节点) |
| **修改** | `src/backend/requirements.txt` |

### Phase 3 涉及文件

| 操作 | 文件路径 |
|---|---|
| **新建** | `src/backend/app/tools/__init__.py` |
| **新建** | `src/backend/app/tools/schema_tools.py` |
| **新建** | `src/backend/app/tools/ddl_tools.py` |
| **新建** | `src/backend/app/tools/deploy_tools.py` |
| **修改** | `src/backend/app/graphs/nodes/` (各 node 升级为 Agent) |
| **新建** | `src/backend/app/graphs/supervisor_graph.py` |
| **修改** | `src/backend/app/graphs/state.py` |
