from core.database import PsqlHelper
from core.log import log
from crud.crud_project import crud_project
from graphs.state import ProjectState
from redis_client.cache_service import cache_service
from redis_client.redis_keys import redis_key_manager
from schema.project import CreationStageEnum
from graphs.db import _get_shared_engine
from service.ai_service import AIService



async def generate_schema_node(state: ProjectState) -> dict:
    """
    调用 AI 生成 schema，更新 state 中的 schema_text 字段，并返回生成的 schema 文本。
    Args:
        state:

    Returns:

    """
    engine = _get_shared_engine()
    project_id = state['project_id']
    try:
        # 更新项目状态为正在生成 Schema
        async with PsqlHelper.get_session(engine) as db:
            await crud_project.update(
                db, project_id,
                creation_stage=CreationStageEnum.GENERATING_SCHEMA.value
            )

        # 调用 AI 服务生成 Schema
        schema_text = await AIService.generate_schema(
            requirements=state["requirements"],
            db_name=state["db_name"],
            db_type=state["db_type"],
            ai_model_hint=state["ai_model"]
        )

        if not schema_text or "error" in schema_text.lower():
            log.error(f"Schema generation failed for project {state['project_id']}")
            return {
                "error_message": f"Schema generation failed: {schema_text}",
                "current_stage": CreationStageEnum.FAILED.value,
            }

        # 保存生成的 Schema
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
                    creation_stage=CreationStageEnum.SCHEMA_GENERATED.value,
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
        log.info(f"[Graph] Schema generated for project {project_id}")
        return {
            "schema_text": schema_text,
            "current_stage": CreationStageEnum.SCHEMA_GENERATED.value,
            "node_history": ["generate_schema"],
        }

    except Exception as e:
        log.exception(f"Schema generation error for project {project_id}")
        async with PsqlHelper.get_session(engine) as db:
            await crud_project.update(
                db, project_id, creation_stage=CreationStageEnum.FAILED.value
            )
        return {
            "error_message": str(e),
            "current_stage": CreationStageEnum.FAILED.value,
            "node_history": ["generate_schema"],
        }