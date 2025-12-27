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
