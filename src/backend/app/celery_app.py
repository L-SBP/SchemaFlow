# backend/app/celery_app.py

"""
Celery 应用配置模块

负责配置和初始化 Celery 异步任务队列
"""

import os
from celery import Celery

# 从环境变量获取 Redis 配置，提供默认值
REDIS_HOST = os.getenv("REDIS__HOST", "localhost")
REDIS_PORT = os.getenv("REDIS__PORT", "6379")

# Celery Broker 和 Backend URL
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")

# 创建 Celery 应用实例
celery_app = Celery(
    "app",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["tasks.ai_generation_tasks"]  # 包含 AI 生成任务模块
)

# Celery 配置
celery_app.conf.update(
    # 任务序列化方式
    task_serializer="json",
    # 结果序列化方式
    result_serializer="json",
    # 接受的内容类型
    accept_content=["json"],
    # 时区设置
    timezone="Asia/Shanghai",
    # 启用 UTC
    enable_utc=True,
    # 任务结果过期时间 (秒)
    result_expires=3600,
    # 任务确认方式：任务完成后确认
    task_acks_late=True,
    # Worker 预取任务数量
    worker_prefetch_multiplier=1,
)
