from celery import Celery
import os

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", "6379")

celery_app = Celery(
    "video_processor",
    broker=f"redis://{redis_host}:{redis_port}/0",
    backend=f"redis://{redis_host}:{redis_port}/1",
    include=[
        "api.tasks.logo_tasks",
        "api.tasks.video_tasks",
        "api.tasks.text_tasks",
        "api.tasks.nsfw_tasks",
        "api.tasks.upload_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=7200,
    task_soft_time_limit=3600,
    worker_concurrency=2,
    result_expires=86400,
)
