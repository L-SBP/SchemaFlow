from core.database import PsqlHelper
from core.log import log
from crud.crud_project import crud_project
from graphs.state import ProjectState
from redis_client.cache_service import cache_service
from redis_client.redis_keys import redis_key_manager
from graphs.db import _get_shared_engine
from service.ai_service import AIService


async def generate_er_node(state: ProjectState) -> dict:
    """调用 AI 生成 Mermaid ER 图"""
    project_id = state["project_id"]
    schema_text = state.get("schema_text", "")
    engine = _get_shared_engine()

    try:
        er_code = await AIService.generate_mermaid_code(
            schema_text=schema_text,
            ai_model_hint=state["ai_model"],
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

        log.info(f"ER diagram generated for project {project_id}")
        return {
            "er_diagram_code": er_code,
            "node_history": ["generate_er"],
        }

    except Exception as e:
        # ER 是非关键步骤，失败不阻断流程
        log.warning(f"ER generation failed (non-critical): {e}")
        return {
            "er_diagram_code": None,
            "node_history": ["generate_er"],
        }