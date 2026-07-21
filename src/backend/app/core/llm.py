from typing import Optional, Dict, Any

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

# ═══════════════════════════════════════════════════
# 任务 → 默认模型映射（优先读 config.yaml，fallback 到代码默认）
# ═══════════════════════════════════════════════════

_FALLBACK_TASK_CONFIG: Dict[str, Any] = {
    "schema_generation": {"model": "deepseek-v3", "temperature": 0.1, "max_tokens": 4096},
    "ddl_generation": {"model": "deepseek-v3", "temperature": 0.0, "max_tokens": 8192},
    "er_generation": {"model": "deepseek-v3", "temperature": 0.2, "max_tokens": 2048},
}


def _load_task_config() -> Dict[str, Any]:
    """加载任务配置：config.yaml > 代码默认"""
    try:
        from core.config import config
        if hasattr(config, "tasks") and config.tasks:
            return config.tasks
    except Exception:
        pass
    return _FALLBACK_TASK_CONFIG


TASK_DEFAULT_MODEL = _load_task_config()


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
    """根据任务获取模型。映射关系来自 TASK_DEFAULT_MODEL，用户传 ai_model 时覆盖。"""
    task_cfg = TASK_DEFAULT_MODEL.get(task_type, {})

    model_name = task_cfg.get("model") or model_registry.get_default_name()
    temperature = task_cfg.get("temperature", 0.1)
    max_tokens = task_cfg.get("max_tokens", 4096)

    return create_chat_model(model_name=model_name,
                             temperature=temperature,
                             max_tokens=max_tokens)


def resolve_model_name(user_hint: Optional[str] = None, task_type: Optional[str] = None) -> str:
    """
    三层 fallback 解析模型名，供 service 层调用。
    优先级：用户传值 > 任务默认配置 > 注册表默认模型
    """
    if user_hint:
        return user_hint
    if task_type:
        task_cfg = TASK_DEFAULT_MODEL.get(task_type, {})
        if task_cfg.get("model"):
            return task_cfg["model"]
    return model_registry.get_default_name()


async def init_model_registry(db):
    """
    启动时从数据库加载所有模型到内存注册表。
    在 server.py startup 中调用。
    """
    from crud.crud_ai_model_config import crud_ai_model_config

    registry_dict = await crud_ai_model_config.get_model_registry(db)
    if not registry_dict:
        # 表为空则写入预设模型后重新加载
        await _seed_preset_models(db)
        registry_dict = await crud_ai_model_config.get_model_registry(db)

    for model_data in registry_dict.values():
        model_registry.register(ModelDef(model_data))


async def _seed_preset_models(db):
    """首次启动时填充预设模型到 ai_model_config 表"""
    import os
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
    ]

    existing_names = set()
    for existing_config in (await db.execute(
        __import__("sqlalchemy").select(AIModelConfig.model_name)
    )).scalars().all():
        existing_names.add(existing_config)

    for p in presets:
        if p.model_name not in existing_names:
            db.add(p)

    await db.commit()