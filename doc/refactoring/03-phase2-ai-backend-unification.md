# 03 — Phase 2: AI 后端统一（外部 API → LangChain）

> **前提**：Phase 1 已完成并验证稳定  
> **原则**：将 3 个外部 AI 微服务替换为 LangChain 统一 LLM 调用  
> **目标**：解除对外部 AI 服务的依赖，所有 AI 调用由本地/云端 LLM 统一管理

---

## 一、现状回顾

### 1.1 Phase 1 后的外部依赖

| 功能 | 当前实现 | 外部依赖 |
|---|---|---|
| Schema 生成 | `AIService.generate_schema()` | `POST http://43.154.73.48:5000/gradio_api/queue/join` |
| DDL 生成 | `AIService.generate_ddl()` | `POST https://schema2ddl.strangeloop.fun/generate/ddl` |
| ER 生成 | `AIService.generate_mermaid_code()` | OpenAI 兼容 API `ai.nengyongai.cn/v1` |

### 1.2 项目已有的模型管理基础设施

**好消息：不需要从零开始。** 项目已经有一套完整的模型配置管理系统：

| 组件 | 文件 | 现有能力 |
|---|---|---|
| DB 表 | `models/ai_model_config.py` | `AIModelConfig` 表：`model_name`, `api_url`, `model_id`, `api_key`, `model_type` |
| CRUD | `crud/crud_ai_model_config.py` | 含 `get_model_registry()` 方法，返回所有配置的注册表 dict |
| API | `api/v1/endpoints/admin.py` | 完整的 admin CRUD 端点 (`GET/POST/PUT/DELETE /admin/ai-models`) |
| 前端 | `frontend/.../AdminAIModels.tsx` | 管理员模型配置页面（增删改查 + 连接测试） |
| 注册表 | `service/chat_service.py:59-91` | `FALLBACK_MODEL_REGISTRY` 后备模型 + `get_model_registry(db)` 动态加载 |
| ORM 方法 | `ai_model_config.py:83` | `to_registry_format()` 转 dict |

当前 `FALLBACK_MODEL_REGISTRY` 的样子（`chat_service.py:59-88`）：

```python
FALLBACK_MODEL_REGISTRY = {
    "my-finetuned-sql": {
        "name": "My Fine-Tuned SQL Model",
        "api_url": "http://1.92.127.206:8080/v1/chat/completions",
        "model_id": "codellama/CodeLlama-13b-Instruct-hf",
        "api_key": "sk-2025texttosql",
        "type": "local_finetune"
    },
    "deepseek-v3": {
        "name": "DeepSeek V3.1",
        "api_url": "https://api-inference.modelscope.cn/v1/chat/completions",
        "model_id": "deepseek-ai/DeepSeek-V3.1",
        "api_key": settings.ai.modelscope_api_key,
        "type": "general_llm"
    },
    # ... 更多模型
}
```

### 1.3 现有表的不足

`AIModelConfig` 表当前能满足 OpenAI 兼容格式的调用（因为整个项目只做 OpenAI 兼容调用），但为了支持 Phase 2 的 Anthropic / Ollama / 通用适配，需要新增字段：

| 当前字段 | 映射到新设计 | 是否够用 |
|---|---|---|
| `model_name` | → `name` (注册名) | ✅ |
| `api_url` | → `base_url` | ✅ |
| `model_id` | → `model_id` | ✅ |
| `api_key` | → API key（存 DB） | ✅ |
| `model_type` | → 保留（`local_finetune` / `general_llm`） | ✅ 保持不变 |
| _(缺失)_ | `provider` | ❌ **需新增** |

---

## 二、改动方案

### 2.1 总体架构

```
数据库 ai_model_config 表（唯一来源，全部放 DB）
┌──────────────────────────────────────────────────────────┐
│ config_id │ model_name  │ provider          │ api_url     │
│───────────│─────────────│───────────────────│─────────────│
│ 1         │ deepseek-v3 │ openai_compatible │ api.deep... │
│ 2         │ gpt-4o      │ openai            │ api.open... │
│ 3         │ claude-son  │ anthropic         │ api.anth... │
│ 4         │ qwen-local  │ ollama            │ localhost   │
│ 5         │ my-vllm     │ openai_compatible │ 10.0.0.5... │
│                                                          │
│ is_preset │ 来源                                           │
│───────────│────────────────────────────────               │
│ true      │ 系统预设（种子数据，不可删除）                   │
│ true      │ 系统预设                                       │
│ true      │ 系统预设                                       │
│ true      │ 系统预设                                       │
│ false     │ 用户/管理员通过前端添加                          │
└──────────────────────────────────────────────────────────┘
         │                              ▲
         │ 启动时加载                     │ 运行时动态添加
         ▼                              │
  ┌─────────────────────────┐    ┌─────────────┐
  │ ModelRegistry           │    │ Admin UI    │
  │ (llm.py，内存注册表)     │    │ (已有！)     │
  │                         │    │ 增删改查模型  │
  │ model_registry.get()    │    └─────────────┘
  │ model_registry.register()
  └───────────┬─────────────┘
              │
              ▼
  ┌─────────────────────────┐
  │ Task → Model 映射        │
  │ config.yaml → tasks      │
  │ schema: deepseek-v3     │
  │ ddl:    claude-son      │
  │ er:     deepseek-v3     │
  └───────────┬─────────────┘
              │
              ▼
  ┌─────────────────────────┐
  │ Provider 适配层          │
  │ openai       → ChatOpenAI│
  │ openai_compat → Chat... │
  │ anthropic    → ChatAnth. │
  │ ollama       → ChatOllama│
  └─────────────────────────┘
```

**不用 `llm_config.yaml`**——全部模型都存 DB。预设模型通过数据库种子数据（migration/seed script）写入。

### 2.2 AIModelConfig 表改动（新增 2 个字段）

```sql
-- 迁移 SQL（新增 provider 和 is_preset 列）
ALTER TABLE ai_model_config 
ADD COLUMN provider VARCHAR(32) NOT NULL DEFAULT 'openai_compatible'
COMMENT '适配器类型: openai | openai_compatible | anthropic | ollama';

ALTER TABLE ai_model_config 
ADD COLUMN is_preset BOOLEAN NOT NULL DEFAULT FALSE
COMMENT '是否系统预设（预设模型前端不可删除）';
```

更新 ORM 模型：

```python
# models/ai_model_config.py — 新增字段

class AIModelConfig(Base):
    __tablename__ = 'ai_model_config'

    config_id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(200), nullable=False, unique=True)
    api_url = Column(String(500), nullable=False)
    model_id = Column(String(200), nullable=False)
    api_key = Column(String(500), nullable=False)
    model_type = Column(String(50), nullable=False, default='general_llm')

    # ════ 新增字段 ════
    provider = Column(
        String(32),
        nullable=False,
        default='openai_compatible',
        comment='适配器: openai | openai_compatible | anthropic | ollama'
    )
    is_preset = Column(
        Boolean,
        nullable=False,
        default=False,
        comment='是否系统预设模型（不可删除）'
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_registry_format(self) -> dict:
        return {
            "name": self.model_name,
            "provider": self.provider,
            "api_url": self.api_url,
            "model_id": self.model_id,
            "api_key": self.api_key,
            "type": self.model_type,
            "is_preset": self.is_preset,
        }
```

### 2.3 Pydantic Schema 新增字段

```python
# schema/ai_model_config.py — 新增字段

class AIModelConfigCreate(BaseModel):
    model_name: str = Field(..., max_length=200)
    api_url: str = Field(..., max_length=500)
    model_id: str = Field(..., max_length=200)
    api_key: str = Field(..., max_length=500)
    model_type: str = Field(default="general_llm")
    provider: str = Field(default="openai_compatible")  # 新增
    model_config = ConfigDict(protected_namespaces=())


class AIModelConfigUpdate(BaseModel):
    model_name: Optional[str] = Field(None, max_length=200)
    api_url: Optional[str] = Field(None, max_length=500)
    model_id: Optional[str] = Field(None, max_length=200)
    api_key: Optional[str] = Field(None, max_length=500)
    model_type: Optional[str] = None
    provider: Optional[str] = None  # 新增
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
```

### 2.4 种子数据 — 替代 FALLBACK_MODEL_REGISTRY

创建 DB migration 脚本，将 `FALLBACK_MODEL_REGISTRY` 中的模型写入 `ai_model_config` 表，并标记 `is_preset=true`：

```python
# 种子脚本 seed_ai_models.py（或写在 Alembic migration 中）

PRESET_MODELS = [
    {
        "model_name": "deepseek-v3",
        "provider": "openai_compatible",
        "model_id": "deepseek-ai/DeepSeek-V3.1",
        "api_url": "https://api-inference.modelscope.cn/v1/chat/completions",
        "api_key": "___FROM_ENV_DEEPSEEK_API_KEY___",
        "model_type": "general_llm",
        "is_preset": True,
    },
    {
        "model_name": "gpt-4o",
        "provider": "openai",
        "model_id": "gpt-4o-2024-08-06",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "api_key": "___FROM_ENV_OPENAI_API_KEY___",
        "model_type": "general_llm",
        "is_preset": True,
    },
    {
        "model_name": "claude-sonnet",
        "provider": "anthropic",
        "model_id": "claude-3-5-sonnet-20241022",
        "api_url": "https://api.anthropic.com/v1/messages",
        "api_key": "___FROM_ENV_ANTHROPIC_API_KEY___",
        "model_type": "general_llm",
        "is_preset": True,
    },
    {
        "model_name": "qwen3-local",
        "provider": "ollama",
        "model_id": "qwen3:32b",
        "api_url": "http://localhost:11434/api/chat",
        "api_key": "ollama",
        "model_type": "general_llm",
        "is_preset": True,
    },
]

# 迁移逻辑：INSERT ... ON CONFLICT (model_name) DO NOTHING
```

启动时：
1. 先跑 seed 确保预设模型存在于 DB
2. `init_model_registry()` 从 DB 加载所有 `is_active` (或所有) 的模型到内存注册表
3. 用户/admin 通过前端添加的模型 `is_preset=false`，动态注入注册表

---

## 三、核心代码

### 3.1 llm.py — 模型注册表 + Provider 工厂

```python
"""LLM 工厂 —— 基于 AIModelConfig 表的统一模型管理"""

import os
from typing import Optional, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import config as app_config


# ═══════════════════════════════════════════════════
# 模型定义（轻量，从 DB 行转换得到）
# ═══════════════════════════════════════════════════

class ModelDef:
    """内存中的模型定义，从 AIModelConfig.to_registry_format() 转换而来"""

    def __init__(self, data: Dict[str, Any]):
        self.name: str = data["name"]
        self.provider: str = data.get("provider", "openai_compatible")
        self.api_url: str = data.get("api_url", "")
        self.model_id: str = data.get("model_id", "")
        self.api_key: str = data.get("api_key", "")
        self.model_type: str = data.get("type", "general_llm")
        self.is_preset: bool = data.get("is_preset", False)


# ═══════════════════════════════════════════════════
# 注册表
# ═══════════════════════════════════════════════════

class ModelRegistry:
    """统一注册表 —— 从 AIModelConfig DB 表加载"""

    def __init__(self):
        self._models: dict[str, ModelDef] = {}
        self._default: Optional[str] = None

    def register(self, m: ModelDef):
        self._models[m.name] = m
        # 第一个注册的设为默认
        if self._default is None:
            self._default = m.name

    def unregister(self, name: str):
        """只允许移除非预设模型"""
        if name in self._models and not self._models[name].is_preset:
            del self._models[name]
            if self._default == name:
                self._default = next(iter(self._models.keys()), None)

    def get(self, name: str) -> ModelDef:
        if name not in self._models:
            available = ", ".join(self._models.keys())
            raise ValueError(f"未知模型 '{name}'，可用: {available}")
        return self._models[name]

    def get_default_name(self) -> str:
        if not self._default or self._default not in self._models:
            if self._models:
                self._default = next(iter(self._models.keys()))
            else:
                raise RuntimeError("没有注册任何模型")
        return self._default

    def list_all(self) -> list[ModelDef]:
        return list(self._models.values())

    def __contains__(self, name: str) -> bool:
        return name in self._models


model_registry = ModelRegistry()


# ═══════════════════════════════════════════════════
# Provider 适配器
# ═══════════════════════════════════════════════════

def _create_openai(m: ModelDef, **kwargs) -> ChatOpenAI:
    return ChatOpenAI(model=m.model_id, api_key=m.api_key,
                       base_url=m.api_url if m.api_url else None, **kwargs)


def _create_openai_compatible(m: ModelDef, **kwargs) -> ChatOpenAI:
    return ChatOpenAI(model=m.model_id, api_key=m.api_key,
                       base_url=m.api_url, **kwargs)


def _create_anthropic(m: ModelDef, **kwargs) -> ChatAnthropic:
    return ChatAnthropic(model=m.model_id, api_key=m.api_key, **kwargs)


def _create_ollama(m: ModelDef, **kwargs) -> ChatOllama:
    num_predict = kwargs.pop("max_tokens", None)
    return ChatOllama(model=m.model_id,
                       base_url=m.api_url.replace("/api/chat", "") if m.api_url else None,
                       temperature=kwargs.pop("temperature", 0.1),
                       num_predict=num_predict, **kwargs)


_PROVIDER_FACTORIES = {
    "openai": _create_openai,
    "openai_compatible": _create_openai_compatible,
    "anthropic": _create_anthropic,
    "ollama": _create_ollama,
}


# ═══════════════════════════════════════════════════
# 公开 API
# ═══════════════════════════════════════════════════

def create_chat_model(
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> BaseChatModel:
    """根据注册名创建 ChatModel。不传 model_name 则用默认模型。"""
    name = model_name or model_registry.get_default_name()
    model_def = model_registry.get(name)

    factory = _PROVIDER_FACTORIES.get(model_def.provider)
    if factory is None:
        raise ValueError(
            f"模型 '{name}' 的 provider '{model_def.provider}' 不受支持，"
            f"支持: {', '.join(_PROVIDER_FACTORIES.keys())}"
        )

    kwargs = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    return factory(model_def, **kwargs)


def get_model_for_task(task_type: str) -> BaseChatModel:
    """根据任务获取模型。映射关系来自 config.yaml → tasks。"""
    tasks_config = getattr(app_config, "tasks", {})
    task_cfg = tasks_config.get(task_type, {})

    model_name = task_cfg.get("model") or model_registry.get_default_name()
    temperature = task_cfg.get("temperature", 0.1)
    max_tokens = task_cfg.get("max_tokens", 4096)

    return create_chat_model(model_name=model_name,
                             temperature=temperature,
                             max_tokens=max_tokens)


# ═══════════════════════════════════════════════════
# 初始化：从 DB 加载所有模型到注册表
# ═══════════════════════════════════════════════════

async def init_model_registry(db: AsyncSession):
    """
    启动时调用。从 ai_model_config 表加载所有模型到内存注册表。
    取代原来 chat_service.py 中的 FALLBACK_MODEL_REGISTRY + get_model_registry() 模式。
    """
    from crud.crud_ai_model_config import crud_ai_model_config
    from models.ai_model_config import AIModelConfig

    # 复用已有的 get_model_registry() 方法
    registry_dict = await crud_ai_model_config.get_model_registry(db)

    if not registry_dict:
        # DB 没有模型 → 运行种子脚本
        from core.log import log
        log.warning("ai_model_config 表为空，运行种子数据 ...")
        await _seed_preset_models(db)
        registry_dict = await crud_ai_model_config.get_model_registry(db)

    for model_data in registry_dict.values():
        model_registry.register(ModelDef(model_data))


async def _seed_preset_models(db: AsyncSession):
    """将预设模型写入 DB（如果表为空）"""
    from models.ai_model_config import AIModelConfig

    presets = [
        AIModelConfig(
            model_name="deepseek-v3",
            provider="openai_compatible",
            model_id="deepseek-ai/DeepSeek-V3.1",
            api_url="https://api-inference.modelscope.cn/v1/chat/completions",
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            model_type="general_llm",
            is_preset=True,
        ),
        # ... 其他预设模型
    ]
    for p in presets:
        db.add(p)
    await db.commit()
```

### 3.2 server.py — 启动时初始化

```python
# server.py → startup_services()

from core.llm import init_model_registry
from core.database import PsqlHelper

async def startup_services(app: FastAPI):
    # ... 现有初始化代码 ...

    # 初始化 LLM 模型注册表（从 AIModelConfig 表加载）
    log.info("initialize LLM model registry from DB")
    async with PsqlHelper.get_session(app.state.psql_engine) as db:
        await init_model_registry(db)
```

### 3.3 AIService — 调用方不感知 Provider 差异

```python
# service/ai_service.py

from core.llm import get_model_for_task, create_chat_model
from core.prompts.schema_prompt import SCHEMA_PROMPT
from core.prompts.ddl_prompt import DDL_PROMPT
from core.prompts.er_prompt import ER_PROMPT


class AIService:

    @staticmethod
    async def generate_schema(requirements, db_type, db_name, ai_model_hint=None):
        llm = (create_chat_model(ai_model_hint, temperature=0.1)
               if ai_model_hint
               else get_model_for_task("schema_generation"))
        chain = SCHEMA_PROMPT | llm
        response = await chain.ainvoke({
            "requirements": requirements, "db_type": db_type, "db_name": db_name,
        })
        return response.content

    @staticmethod
    async def generate_ddl(schema_text, requirements, db_type, db_name, ai_model_hint=None):
        llm = (create_chat_model(ai_model_hint, temperature=0.0)
               if ai_model_hint
               else get_model_for_task("ddl_generation"))
        chain = DDL_PROMPT | llm
        response = await chain.ainvoke({
            "schema_text": schema_text, "db_type": db_type, "db_name": db_name,
        })
        return _clean_ddl_output(response.content)

    @staticmethod
    async def generate_mermaid_code(schema_text, ai_model_hint=None):
        llm = (create_chat_model(ai_model_hint, temperature=0.2)
               if ai_model_hint
               else get_model_for_task("er_generation"))
        chain = ER_PROMPT | llm
        response = await chain.ainvoke({"schema_text": schema_text})
        return _extract_mermaid_block(response.content)


def _clean_ddl_output(ddl_text: str) -> str:
    ddl_text = ddl_text.strip()
    if ddl_text.startswith("```sql"): ddl_text = ddl_text[6:]
    elif ddl_text.startswith("```"): ddl_text = ddl_text[3:]
    if ddl_text.endswith("```"): ddl_text = ddl_text[:-3]
    return ddl_text.strip()


def _extract_mermaid_block(er_text: str) -> str:
    import re
    match = re.search(r'```(?:mermaid)?\s*(.*?)\s*```', er_text, re.DOTALL)
    return match.group(1).strip() if match else er_text.strip()
```

### 3.4 前端模型管理端点适配

已有的 `/admin/ai-models` CRUD 端点需要少量适配：

```python
# api/v1/endpoints/admin.py — 在创建模型时同步注入运行时注册表

from core.llm import model_registry, ModelDef

@router.post("/ai-models", ...)
async def create_ai_model(data: AIModelConfigCreate, db=Depends(get_db), ...):
    # ... 现有创建逻辑 ...
    config = await crud_ai_model_config.create(db, data)

    # 动态注入运行时注册表（无需重启）
    model_registry.register(ModelDef(config.to_registry_format()))

    return ...

@router.delete("/ai-models/{config_id}", ...)
async def delete_ai_model(config_id: int, db=Depends(get_db), ...):
    config = await crud_ai_model_config.get(db, config_id)
    # 禁止删除系统预设
    if config.is_preset:
        raise HTTPException(403, "系统预设模型不可删除")

    await crud_ai_model_config.delete(db, config_id)
    model_registry.unregister(config.model_name)
    return ...
```

---

## 四、Prompt Template

### 4.1 schema_prompt.py

```python
from langchain_core.prompts import ChatPromptTemplate

SCHEMA_SYSTEM_PROMPT = """你是一位资深数据库架构师。根据用户的需求描述，生成一份完整、规范的数据库逻辑 Schema 定义。

要求：
1. 列出所有表及其字段定义（字段名、类型、约束、注释）
2. 明确主键、外键关系
3. 约定命名规范（表名小写、下划线分割）
4. 考虑索引设计
5. 输出格式为清晰的 Markdown 表格

数据库类型：{db_type}
数据库名称：{db_name}
"""

SCHEMA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SCHEMA_SYSTEM_PROMPT),
    ("user", "{requirements}"),
])
```

### 4.2 ddl_prompt.py

```python
from langchain_core.prompts import ChatPromptTemplate

DDL_SYSTEM_PROMPT = """你是一位数据库 DBA 专家。根据给定的逻辑 Schema 定义，生成可直接执行的 DDL SQL 语句。

要求：
1. 使用 {db_type} 语法
2. 包含 CREATE TABLE、主键、外键、索引
3. 按依赖关系排序（被引用的表先创建）
4. 只输出纯 SQL，不要 Markdown 代码块包裹，不要注释
5. 每个语句以分号结尾

数据库名称：{db_name}
"""

DDL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", DDL_SYSTEM_PROMPT),
    ("user", "Schema 定义：\n\n{schema_text}"),
])
```

### 4.3 er_prompt.py

```python
from langchain_core.prompts import ChatPromptTemplate

ER_SYSTEM_PROMPT = """你是一位数据库可视化专家。根据给定的 Schema 定义，生成 Mermaid ER 图代码。

要求：
1. 使用 erDiagram 语法
2. 每个实体列出关键字段
3. 标注实体间关系（一对一、一对多、多对多）
4. 只输出有效的 Mermaid 代码，不要任何解释文字
"""

ER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", ER_SYSTEM_PROMPT),
    ("user", "请为以下 Schema 生成 Mermaid ER 图：\n\n{schema_text}"),
])
```

---

## 五、config.yaml 变更

只新增 `tasks` 节点（模型列表全部在 DB 的 `ai_model_config` 表中）：

```yaml
# config.yaml 新增
tasks:
  schema_generation:
    model: deepseek-v3          # 引用 ai_model_config.model_name
    temperature: 0.1
    max_tokens: 4096

  ddl_generation:
    model: deepseek-v3
    temperature: 0.0
    max_tokens: 8192

  er_generation:
    model: deepseek-v3
    temperature: 0.2
    max_tokens: 2048
```

---

## 六、改动文件清单

| 操作 | 文件 | 说明 |
|---|---|---|
| **重写** | `src/backend/app/service/ai_service.py` | 改用 `get_model_for_task()` / `create_chat_model()` |
| **新建** | `src/backend/app/core/llm.py` | ModelRegistry + Provider 工厂 |
| **新建** | `src/backend/app/core/prompts/__init__.py` | |
| **新建** | `src/backend/app/core/prompts/schema_prompt.py` | |
| **新建** | `src/backend/app/core/prompts/ddl_prompt.py` | |
| **新建** | `src/backend/app/core/prompts/er_prompt.py` | |
| **修改** | `src/backend/app/models/ai_model_config.py` | 新增 `provider`、`is_preset` 字段 |
| **修改** | `src/backend/app/schema/ai_model_config.py` | Pydantic schema 新增字段 |
| **修改** | `src/backend/app/api/v1/endpoints/admin.py` | 创建模型时动态注入注册表 + 预设保护 |
| **修改** | `src/backend/app/server.py` | startup 调用 `init_model_registry(db)` |
| **修改** | `src/backend/config.yaml` | 新增 `tasks` 节点 |
| **修改** | `src/backend/requirements.txt` | 新增 `langchain-openai`, `langchain-anthropic`, `langchain-ollama` |
| **归档** | `src/backend/app/service/chat_service.py:59-91` | 删除 `FALLBACK_MODEL_REGISTRY` 硬编码（已迁移到 DB seed） |
| **新建** | `src/backend/app/core/seed_ai_models.py` | DB 种子脚本 |

### 验证 Checklist

- [ ] `AIModelConfig` 表新增 `provider`、`is_preset` 字段且向后兼容（有默认值）
- [ ] 种子数据正确写入 DB，启动后 `model_registry` 包含所有预设模型
- [ ] 用户通过 Admin UI 添加的模型**无需重启**即可在注册表中生效
- [ ] 系统预设模型（`is_preset=true`）**不可被删除**
- [ ] OpenAI / Anthropic / Ollama / openai_compatible 四种 provider 均可正常创建 ChatModel
- [ ] `config.yaml → tasks` 中的 `model` 可引用任意 `ai_model_config.model_name`
- [ ] Schema/DDL/ER 生成质量不低于原外部 API
- [ ] 删除 `FALLBACK_MODEL_REGISTRY` 后 chat_service 仍能正常工作（改用新注册表）
