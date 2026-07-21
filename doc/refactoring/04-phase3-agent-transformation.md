# 04 — Phase 3: Agent 化改造（Task → LLM Agent）

> **前提**：Phase 1 和 Phase 2 均已完成并稳定  
> **目标**：将每个处理节点升级为真正的 LLM Agent，具备 tool calling、自主推理、多 Agent 协作能力  
> **改动范围**：新增 tools 层、升级 node 为 Agent、引入 Supervisor + Subgraph 协作模式、Checkpoint 持久化

---

## 一、什么是 Agent 化

当前（Phase 2 之后），每个 node 的工作方式是：

```
输入 state → 拼 prompt → 调 LLM → 返回文本 → 写入 DB
```

Agent 化后的工作方式是：

```
输入 state → Agent 推理 → 选择 tool → 执行 tool → 观察结果 → 继续推理
                                                              ↓
                                                    达到目标 → 返回结果 → 写入 DB
```

**核心变化**：从"一次 LLM 调用"变为"LLM 主导的多次推理 + 工具调用循环"。

---

## 二、Agent 设计

### 2.1 Schema Agent

**职责**：根据用户需求，迭代生成并优化数据库 Schema

**工具列表**：

| 工具名 | 功能 | 输入 | 输出 |
|---|---|---|---|
| `validate_schema` | 验证 Schema 结构合法性 | schema_text | 校验结果 (pass/fail + 问题列表) |
| `search_knowledge_base` | 查询 ChromaDB 领域知识 | query | 相关最佳实践/范例 |
| `list_common_patterns` | 列出常见业务建模模式 | 业务类型 | 推荐的 Schema 模式 |
| `check_naming_convention` | 检查命名规范 | schema_text | 不符合规范的项目列表 |

**工作流**：

```
Schema Agent
├── 1. 理解用户需求
├── 2. 查询知识库 (search_knowledge_base)
├── 3. 获取推荐模式 (list_common_patterns)
├── 4. 生成初始 Schema
├── 5. 校验 Schema (validate_schema)
├── 6. 检查命名规范 (check_naming_convention)
├── 7. 如有问题 → 回到步骤 4 迭代修正
└── 8. 输出最终 Schema
```

### 2.2 DDL Agent

**职责**：根据 Schema 生成正确、可执行的 DDL

**工具列表**：

| 工具名 | 功能 | 输入 | 输出 |
|---|---|---|---|
| `validate_sql_syntax` | 使用 sqlglot 验证 SQL 语法 | ddl_text, db_type | 语法错误列表 |
| `check_foreign_key_order` | 检查表创建顺序（外键引用关系） | ddl_text | 重排后的 DDL |
| `get_db_metadata` | 查询目标数据库现有表结构 | project_id | 已存在的表清单 |
| `check_index_redundancy` | 检查索引是否冗余/缺失 | ddl_text | 索引建议 |

**工作流**：

```
DDL Agent
├── 1. 读取 Schema 定义
├── 2. 查询现有表结构 (get_db_metadata)
├── 3. 生成初始 DDL
├── 4. 验证 SQL 语法 (validate_sql_syntax)
├── 5. 检查外键顺序 (check_foreign_key_order)
├── 6. 检查索引设计 (check_index_redundancy)
├── 7. 如有问题 → 回到步骤 3 修正
└── 8. 输出最终 DDL
```

### 2.3 Deploy Agent

**职责**：安全部署 DDL，处理错误并自动修复

**工具列表**：

| 工具名 | 功能 | 输入 | 输出 |
|---|---|---|---|
| `execute_ddl_batch` | 逐条执行 DDL 语句 | ddl_text, db_type | 每条语句的执行状态 |
| `rollback_last` | 回滚最后一条语句 | session_id | 回滚结果 |
| `diagnose_error` | 分析执行错误原因 | error_message, ddl_statement | 原因分析 + 修复建议 |
| `check_db_connection` | 检查数据库连接是否正常 | db_type | 连接状态 |

**工作流**：

```
Deploy Agent
├── 1. 检查数据库连接 (check_db_connection)
├── 2. 逐条执行 DDL (execute_ddl_batch)
├── 3. 遇到错误 → 诊断错误 (diagnose_error)
├── 4. 根据诊断 → 自动修正 DDL
├── 5. 修正后 → 回到步骤 2 重试
├── 6. 无法自动修复 → 请求人工介入 (Human-in-the-Loop)
└── 7. 全部部署成功 → 完成
```

---

## 三、目录结构

Phase 3 新增文件：

```
src/backend/app/
├── tools/                          # 新建：Agent 工具层
│   ├── __init__.py
│   ├── schema_tools.py             # Schema Agent 工具
│   ├── ddl_tools.py                # DDL Agent 工具
│   └── deploy_tools.py             # Deploy Agent 工具
├── graphs/
│   ├── agents/                     # 新建：Agent 定义
│   │   ├── __init__.py
│   │   ├── schema_agent.py         # Schema Agent (含 tool binding)
│   │   ├── ddl_agent.py            # DDL Agent
│   │   └── deploy_agent.py         # Deploy Agent
│   └── supervisor_graph.py         # 新建：Supervisor 编排图
```

---

## 四、Agent 实现示例

### 4.1 Schema Agent

```python
"""Schema Agent —— 迭代生成 Schema 的 LLM Agent"""

from langgraph.prebuilt import create_react_agent
from core.llm import get_llm
from tools.schema_tools import (
    validate_schema,
    search_knowledge_base,
    list_common_patterns,
    check_naming_convention,
)
from core.prompts.schema_prompt import SCHEMA_SYSTEM_PROMPT


def create_schema_agent(ai_model: str = "deepseek"):
    """创建 Schema Agent"""
    llm = get_llm(ai_model, temperature=0.1)

    tools = [
        validate_schema,
        search_knowledge_base,
        list_common_patterns,
        check_naming_convention,
    ]

    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=SCHEMA_SYSTEM_PROMPT,
    )
```

### 4.2 工具示例

```python
"""Schema Agent 工具"""

from langchain_core.tools import tool
from sqlglot import parse_one
from sqlglot.errors import ErrorLevel


@tool
def validate_schema(schema_text: str, db_type: str) -> str:
    """
    验证 Schema 的结构合法性。
    
    Args:
        schema_text: Schema 文本定义
        db_type: 目标数据库类型 (mysql/postgresql/sqlite)
    
    Returns:
        校验结果（通过/失败 + 具体问题列表）
    """
    # 1. 尝试解析每条 DDL
    issues = []
    statements = [s.strip() for s in schema_text.split(';') if s.strip()]

    for stmt in statements:
        try:
            parse_one(stmt, read=db_type, error_level=ErrorLevel.RAISE)
        except Exception as e:
            issues.append(f"语法错误: {e}\n语句: {stmt[:100]}")

    if issues:
        return f"校验失败，发现 {len(issues)} 个问题:\n" + "\n".join(issues)
    return "校验通过"


@tool
def search_knowledge_base(query: str) -> str:
    """在 ChromaDB 领域知识库中搜索相关最佳实践"""
    from service.rag_service import RAGService
    results = RAGService.search_knowledge(query, top_k=3)
    if not results:
        return "未找到相关最佳实践。"
    return "\n\n".join([f"【{i+1}】{r['content']}" for i, r in enumerate(results)])


@tool
def list_common_patterns(business_type: str) -> str:
    """列出常见业务场景的推荐数据库设计模式"""
    patterns = {
        "电商": "- 用户表 + 订单表 + 商品表 + 订单明细表\n- 需考虑：地址表、支付记录表、购物车表",
        "博客": "- 用户表 + 文章表 + 评论表 + 分类表\n- 需考虑：标签表、文章-标签关联表",
        "权限系统": "- 用户表 + 角色表 + 权限表 + 用户-角色关联表 + 角色-权限关联表",
        "通用": "- 所有表必有 id 主键 (BIGINT AUTO_INCREMENT)\n- 所有表必有 created_at, updated_at 时间戳",
    }
    return patterns.get(business_type, patterns["通用"])


@tool
def check_naming_convention(schema_text: str) -> str:
    """检查命名规范：表名小写下划线、字段名小写下划线、主键统一命名"""
    issues = []
    if 'ID' in schema_text or 'Id' in schema_text:
        issues.append("- 存在大写字段名，建议统一小写 id")
    if not any(word in schema_text for word in ['created_at', 'updated_at']):
        issues.append("- 建议每张表添加 created_at 和 updated_at 字段")
    if issues:
        return "命名规范问题:\n" + "\n".join(issues)
    return "命名规范检查通过"
```

### 4.3 Supervisor Graph

```python
"""Supervisor 图 —— 协调多个 Agent 的编排器"""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from graphs.state import ProjectState
from graphs.agents.schema_agent import create_schema_agent
from graphs.agents.ddl_agent import create_ddl_agent
from graphs.agents.deploy_agent import create_deploy_agent


def supervisor_route(state: ProjectState) -> Literal[
    "schema_agent", "ddl_agent", "deploy_agent", "human_confirm", END
]:
    """Supervisor 路由逻辑 —— 根据当前阶段决定下个 Agent"""
    stage = state.get("current_stage", "")

    routing = {
        "generating_schema": "schema_agent",
        "schema_generated": "human_confirm",   # 等用户确认
        "user_confirmed": "ddl_agent",
        "ddl_generated": "human_confirm",       # 等用户确认
        "ready_to_deploy": "deploy_agent",
        "completed": END,
    }
    return routing.get(stage, END)


def build_supervisor_graph(checkpointer=None):
    """构建 Supervisor 多 Agent 编排图"""

    builder = StateGraph(ProjectState)

    # 各 Agent 作为 Subgraph
    builder.add_node("schema_agent", create_schema_agent())
    builder.add_node("ddl_agent", create_ddl_agent())
    builder.add_node("deploy_agent", create_deploy_agent())

    # Human-in-the-Loop 节点：等待用户确认后继续
    builder.add_node("human_confirm", _human_confirm_node)

    builder.add_edge(START, "schema_agent")

    # Supervisor 动态路由
    builder.add_conditional_edges("schema_agent", supervisor_route)
    builder.add_conditional_edges("human_confirm", supervisor_route)
    builder.add_conditional_edges("ddl_agent", supervisor_route)
    builder.add_conditional_edges("deploy_agent", supervisor_route)

    return builder.compile(checkpointer=checkpointer)


def _human_confirm_node(state: ProjectState) -> dict:
    """
    Human-in-the-Loop 确认节点。
    实际实现中，此节点会中断 graph 执行，等待外部 API 调用恢复。
    LangGraph 支持 interrupt() 机制实现。
    """
    from langgraph.types import interrupt

    current_stage = state.get("current_stage", "")
    if current_stage == "schema_generated":
        schema = state.get("schema_text", "")
        approved = interrupt(f"请确认 Schema:\n{schema[:500]}...")
        if approved:
            return {"current_stage": "user_confirmed"}
        return {"current_stage": "generating_schema"}  # 回退重生成

    if current_stage == "ddl_generated":
        ddl = state.get("ddl_statement", "")
        approved = interrupt(f"请确认 DDL:\n{ddl[:500]}...")
        if approved:
            return {"current_stage": "ready_to_deploy"}
        return {"current_stage": "ddl_generated"}  # 回退重生成

    return {}
```

---

## 五、Checkpoint 持久化

### 5.1 配置 PostgresSaver

```python
# app/graphs/checkpoint.py

from langgraph.checkpoint.postgres import PostgresSaver
from app.core.database import get_sync_db_url

_checkpointer_instance = None


def get_checkpointer() -> PostgresSaver:
    """获取全局 checkpoint 实例（单例）"""
    global _checkpointer_instance
    if _checkpointer_instance is None:
        db_url = get_sync_db_url()
        _checkpointer_instance = PostgresSaver.from_conn_string(db_url)
        _checkpointer_instance.setup()
    return _checkpointer_instance
```

### 5.2 在 Service 层使用 checkpoint

```python
# project_service.py 中

from graphs.supervisor_graph import build_supervisor_graph
from graphs.checkpoint import get_checkpointer


async def _run_graph_with_checkpoint(task_id: str, state: ProjectState):
    """使用 checkpoint 持久化执行 graph"""
    checkpointer = get_checkpointer()
    graph = build_supervisor_graph(checkpointer=checkpointer)

    # 使用 thread_id 关联多轮交互
    config = {"configurable": {"thread_id": str(state["project_id"])}}

    async for event in graph.astream(state, config=config):
        # event 中包含每个 node 的执行结果
        _running_tasks[task_id] = {
            "status": "RUNNING",
            "project_id": state["project_id"],
            "current_event": event,
        }

    # 获取最终状态
    final_state = graph.get_state(config)
    _running_tasks[task_id] = {
        "status": "SUCCESS",
        "project_id": state["project_id"],
        "result": final_state.values,
    }
```

---

## 六、Human-in-the-Loop 机制

这是 Phase 3 的关键特性，替代原来的"生成完→用户手动发请求确认"模式：

```
Graph 执行到 human_confirm 节点 → interrupt() 暂停
                                    ↓
                          前端收到 "等待确认" 状态
                          展示 Schema/DDL 给用户审查
                                    ↓
                          用户点击"确认" → POST /projects/{id}/confirm
                                    ↓
                          API 调用 graph.update_state() 继续执行
```

**API 端点设计**：

```python
@router.post("/projects/{project_id}/confirm")
async def confirm_project(project_id: int, action: str = "approve"):
    """
    确认/拒绝 Schema 或 DDL
    action: "approve" | "reject"
    """
    checkpointer = get_checkpointer()
    config = {"configurable": {"thread_id": str(project_id)}}

    state = graph.get_state(config)
    # 恢复 graph 执行，传入用户决策
    await graph.aupdate_state(config, {"user_approval": (action == "approve")})

    # 继续执行到下一个 Human-in-the-Loop 点或结束
    async for event in graph.astream(None, config=config):
        ...
```

---

## 七、改动文件清单

| 操作 | 文件 |
|---|---|
| **新建** | `src/backend/app/tools/__init__.py` |
| **新建** | `src/backend/app/tools/schema_tools.py` |
| **新建** | `src/backend/app/tools/ddl_tools.py` |
| **新建** | `src/backend/app/tools/deploy_tools.py` |
| **新建** | `src/backend/app/graphs/agents/__init__.py` |
| **新建** | `src/backend/app/graphs/agents/schema_agent.py` |
| **新建** | `src/backend/app/graphs/agents/ddl_agent.py` |
| **新建** | `src/backend/app/graphs/agents/deploy_agent.py` |
| **新建** | `src/backend/app/graphs/supervisor_graph.py` |
| **新建** | `src/backend/app/graphs/checkpoint.py` |
| **修改** | `src/backend/app/graphs/state.py` (新增 `user_approval` 字段) |
| **修改** | `src/backend/app/service/project_service.py` |
| **修改** | `src/backend/app/api/v1/projects.py` (新增 confirm 端点) |

Phase 3 不删除 Phase 2 的 `graphs/nodes/` 旧文件，保持双轨运行一段时间后清理。

---

## 八、Phase 3 验证 Checklist

- [ ] Schema Agent 能通过 tool calling 迭代优化 Schema
- [ ] DDL Agent 能通过 `validate_sql_syntax` 工具发现并修复问题
- [ ] Deploy Agent 能在部署失败后自动诊断
- [ ] Supervisor 图正确路由到各 Agent
- [ ] Human-in-the-Loop 节点能暂停并等待外部恢复
- [ ] Checkpoint 持久化 —— 进程重启后能恢复未完成的 graph 执行
- [ ] 前端 `/confirm` 端点可用
