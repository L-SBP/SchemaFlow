from core.database import PsqlHelper
from core.log import log
from crud.crud_project import crud_project
from graphs.state import ProjectState
from redis_client.cache_service import cache_service
from redis_client.redis_keys import redis_key_manager
from schema.project import CreationStageEnum
from server import my_app
from service.ai_service import AIService


async def generate_ddl_node(state: ProjectState) -> dict:
    """调用 AI 生成 DDL 语句"""
    project_id = state["project_id"]
    schema_text = state.get("schema_text", "")
    engine = my_app.state.psql_engine

    try:
        # 1. 更新阶段状态
        async with PsqlHelper.get_session(engine) as db:
            await crud_project.update(
                db, project_id,
                creation_stage=CreationStageEnum.GENERATING_DDL.value
            )

        # 2. 调用 AI 生成 DDL
        ddl = await AIService.generate_ddl(
            schema_text=schema_text,
            requirements=state["requirements"],
            db_type=state["db_type"],
            ai_model=state["ai_model"],
        )

        if not ddl or "error" in ddl.lower():
            log.error(f"DDL generation failed for project {project_id}")
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
                creation_stage=CreationStageEnum.DDL_GENERATED.value,
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
        log.info(f"[Graph] DDL generated for project {project_id}")
        return {
            "ddl_statement": ddl,
            "current_stage": "ddl_generated",
            "node_history": ["generate_ddl"],
        }

    except Exception as e:
        log.exception(f"DDL generation error for project {project_id}")
        async with PsqlHelper.get_session(engine) as db:
            await crud_project.update(db, project_id, creation_stage="failed")
        return {
            "error_message": str(e),
            "current_stage": "failed",
            "node_history": ["generate_ddl"],
        }