import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Video Processing API"
    api_version: str = "v1"
    debug: bool = True
    
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    
    celery_broker_url: str = os.getenv(
        "CELERY_BROKER_URL",
        f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/0"
    )
    celery_result_backend: str = os.getenv(
        "CELERY_RESULT_BACKEND",
        f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/1"
    )
    
    downloads_dir: str = "/home/node/downloads"
    models_dir: str = "/data/models"
    tmp_dir: str = "/tmp"
    
    task_time_limit: int = 7200
    task_soft_time_limit: int = 3600
    worker_concurrency: int = 2

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
