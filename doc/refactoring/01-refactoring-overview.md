# 01 — 重构总览

---

## 一、现状分析

### 1.1 项目概况

SchemaFlow 是一个 AI 驱动的数据库自动部署系统。用户输入业务需求描述 → 系统自动生成数据库 Schema → 用户确认后生成 DDL → 一键部署到 MySQL/PostgreSQL/SQLite。

当前项目采用 **FastAPI + Celery + Redis + PostgreSQL** 架构，Celery 负责异步任务编排。

### 1.2 当前 Celery 编排架构

```
┌────────────────────────────────────────────────────────────┐
│  FRONTEND (React)                                          │
│  POST /projects/  →  轮询 GET /projects/tasks/{task_id}    │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│  FASTAPI (app/server.py)                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Service Layer (project_service.py)                  │  │
│  │  _dispatch_schema_er_task() → task.delay()           │  │
│  │  _dispatch_ddl_er_task()   → task.delay()            │  │
│  │  _dispatch_er_only_task()  → task.delay()            │  │
│  └──────────────────────┬───────────────────────────────┘  │
└──────────────────────────┼─────────────────────────────────┘
                           │ Redis Broker
                           ▼
┌────────────────────────────────────────────────────────────┐
│  CELERY WORKER (独立进程)                                  │
│  celery -A celery_app worker -Q celery,default,ai_tasks    │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ai_generation_tasks.py (5个Task)                    │  │
│  │                                                      │  │
│  │  Orchestrator Tasks:                                 │  │
│  │  ┌─────────────────────────────────────────────┐    │  │
│  │  │  schema_er_pipeline_task                    │    │  │
│  │  │  ├─ generate_schema_task (手动await)        │    │  │
│  │  │  └─ generate_er_task    (手动await)         │    │  │
│  │  └─────────────────────────────────────────────┘    │  │
│  │  ┌─────────────────────────────────────────────┐    │  │
│  │  │  ddl_er_parallel_task                       │    │  │
│  │  │  ├─ generate_ddl_task  (手动await)          │    │  │
│  │  │  └─ generate_er_task   (条件执行)            │    │  │
│  │  └─────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│  外部 AI 服务                                              │
│  ┌─────────────────┐ ┌──────────────┐ ┌────────────────┐  │
│  │ Gradio API      │ │ schema2ddl   │ │ OpenAI 兼容    │  │
│  │ 43.154.73.48    │ │ .strangeloop │ │ ai.nengyongai  │  │
│  │ Schema 生成     │ │ DDL 生成     │ │ ER 生成        │  │
│  └─────────────────┘ └──────────────┘ └────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### 1.3 当前痛点

**编排层问题**
- `schema_er_pipeline_task` 和 `ddl_er_parallel_task` 中手写 try/except + 顺序调用，逻辑与错误处理混在一起（单个函数 150+ 行）
- 添加新步骤（如 Schema 校验）需要改动 orchestrator task 的整个控制流
- 状态通过直接写 DB (`creation_stage` 字段) 管理，与编排逻辑耦合

**模型选择问题**
- 项目分两个阶段的 AI 模型使用，机制不统一：
  - **建库阶段**（Schema/DDL/ER 生成）：`project_service.py:369` `pop` 掉用户传的 `ai_model`，硬编码为 `"gpt4"`，用户无法选择模型
  - **对话阶段**（Chat/SQL 生成）：通过 `AIModelConfig` 表动态加载，用户可以随时切换模型
- 两个阶段各用一套模型管理机制，维护成本高

**外部服务问题**
- Gradio Schema API (`43.154.73.48:5000`) 不可控，需要 queue/join 轮询等待
- DDL API (`schema2ddl.strangeloop.fun`) 不可控
- 3 个不同地址的 AI 服务，配置和错误处理各异

**架构问题**
- Celery worker 需要独立进程/容器，增加部署复杂度
- 前端通过轮询 task_id 获取状态，用户体验差
- 无法支持 LLM 级别的自主推理和工具使用

---

## 二、目标架构

### 2.1 Phase 1 目标架构（Celery → LangGraph）

```
┌────────────────────────────────────────────────────────────┐
│  FASTAPI (app/server.py)                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Service Layer (project_service.py)                  │  │
│  │  graph.ainvoke(state) / graph.astream(state)         │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│                         ▼ (同进程 asyncio)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LangGraph Graphs (app/graphs/)                      │  │
│  │                                                      │  │
│  │  schema_er_graph.py           ddl_er_graph.py        │  │
│  │  ┌─────────────────┐          ┌─────────────────┐    │  │
│  │  │ START           │          │ START           │    │  │
│  │  │  │              │          │  │              │    │  │
│  │  │  ▼              │          │  ▼              │    │  │
│  │  │ generate_schema │          │ generate_ddl    │    │  │
│  │  │  │              │          │  │              │    │  │
│  │  │  ▼ (条件)       │          │  ▼ (条件)       │    │  │
│  │  │ generate_er ────│          │ generate_er ────│    │  │
│  │  │  │              │          │  │              │    │  │
│  │  │  ▼              │          │  ▼              │    │  │
│  │  │ END             │          │ END             │    │  │
│  │  └─────────────────┘          └─────────────────┘    │  │
│  │                                                      │  │
│  │  Nodes (app/graphs/nodes/)                           │  │
│  │  ┌─────────────┐ ┌──────────┐ ┌──────────┐          │  │
│  │  │schema_node  │ │ er_node  │ │ ddl_node │          │  │
│  │  │→ AIService  │ │→ AIService│ → AIService│          │  │
│  │  │→ DB update  │ │→ DB update│ → DB update│          │  │
│  │  └─────────────┘ └──────────┘ └──────────┘          │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### 2.2 Phase 2 目标架构（外部 API → LangChain）

```
┌───────────────────────────────────────────────────────┐
│  LangChain LLM Factory (app/core/llm.py)              │
│  ┌─────────────────────────────────────────────────┐  │
│  │  get_llm(model_name, temperature, ...)           │  │
│  │  ├─ ollama: "ollama/qwen3:32b"                  │  │
│  │  ├─ openai: "openai/gpt-4o"                     │  │
│  │  └─ deepseek: "deepseek/deepseek-v3"            │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
│  Prompt Templates (app/core/prompts/)                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐        │
│  │ schema     │ │ ddl        │ │ er         │        │
│  │ prompt     │ │ prompt     │ │ prompt     │        │
│  └────────────┘ └────────────┘ └────────────┘        │
└───────────────────────────────────────────────────────┘
```

### 2.3 Phase 3 目标架构（Task → LLM Agent）

```
┌────────────────────────────────────────────────────────────┐
│  Supervisor Graph (app/graphs/supervisor_graph.py)         │
│                                                            │
│                      ┌──────────┐                          │
│                      │Supervisor│                          │
│                      │  Agent   │                          │
│                      └──┬─┬─┬──┘                          │
│                         │ │ │                              │
│           ┌─────────────┘ │ └─────────────┐                │
│           ▼               ▼               ▼                │
│    ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│    │  Schema    │  │   DDL      │  │  Deploy    │         │
│    │  Agent     │  │   Agent    │  │  Agent     │         │
│    │            │  │            │  │            │         │
│    │ Tools:     │  │ Tools:     │  │ Tools:     │         │
│    │ - 查知识库 │  │ - 验证语法 │  │ - 执行DDL  │         │
│    │ - 校验结构 │  │ - 查元数据 │  │ - 检测错误 │         │
│    │ - 最佳实践 │  │ - 自动修复 │  │ - 自动回滚 │         │
│    └────────────┘  └────────────┘  └────────────┘         │
│                                                            │
│    Human-in-the-Loop Checkpoints:                          │
│    ┌─────────────────────────────────────────┐            │
│    │ Schema 生成完 → 等待用户确认 → 继续 DDL │            │
│    │ DDL 生成完   → 等待用户确认 → 继续部署  │            │
│    └─────────────────────────────────────────┘            │
└────────────────────────────────────────────────────────────┘
```

---

## 三、新旧架构对比

| 维度 | 当前 (Celery) | 目标 Phase 1 (LangGraph) | 目标 Phase 2+ |
|---|---|---|---|
| 编排方式 | Celery Task 手写链式调用 | LangGraph 声明式 Graph + 条件边 | LangGraph + Agent Subgraph |
| 状态管理 | DB `creation_stage` 字段 | LangGraph State (TypedDict) | LangGraph Checkpoint |
| 错误处理 | try/except + retry 装饰器 | retry node + fallback 路由 | Agent 自主 retry + 工具反馈 |
| 流程可视化 | 无 | LangGraph graph.get_graph() | LangGraph Studio |
| 可扩展性 | 改动 orchestrator 函数 | 添加/删除 node + edge | 添加 Agent + tool |
| 部署复杂度 | FastAPI + Celery Worker + Redis | FastAPI (单进程) | FastAPI (单进程) |
| AI 调用 | 3 个外部 HTTP API | Phase 1 不变 / Phase 2 LangChain | LangChain + tool calling |
| 前端通信 | HTTP 轮询 task_id | 兼容轮询 (后续改 SSE) | SSE 流式推送 |

---

## 四、风险与对策

| 风险 | 影响 | 对策 |
|---|---|---|
| LangGraph 学习曲线 | 开发效率短期下降 | Phase 1 先做最简实现，逐步深入 |
| 原项目组成员无法接手 | 重构后需自行维护 | 文档先行、注释充分 |
| 外部 AI API 不可用 | Phase 1 期间受影响 | 尽快进入 Phase 2 脱离外部依赖 |
| Schema 生成质量下降 | 业务功能受损 | Phase 2 保留旧 AI service 作为 fallback |
| 前端兼容性问题 | 前后端联调失败 | 严格保持 API 接口签名不变 (Phase 1) |

---

## 五、Phase 严格分离原则

根据决策，**Phase 1 和 Phase 2 严格分开执行**：

1. Phase 1 **只换编排层**，不修改 AI service 任何代码
2. Phase 1 完成后验证全部功能正常
3. 确认稳定后，再开始 Phase 2 替换 AI 后端
4. 每次改动范围小、可回滚、容易定位问题
