# backend/app/tasks/__init__.py

"""
Celery 任务模块

在此文件中定义和导入所有 Celery 异步任务
"""

# 导入 AI 生成任务
from tasks.ai_generation_tasks import (
    generate_schema_task,
    generate_er_task,
    generate_ddl_task,
    schema_er_pipeline_task,
    ddl_er_parallel_task,
    get_task_status,
)

__all__ = [
    "generate_schema_task",
    "generate_er_task", 
    "generate_ddl_task",
    "schema_er_pipeline_task",
    "ddl_er_parallel_task",
    "get_task_status",
]