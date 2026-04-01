from celery import Celery
import os

# ✅ Use env variable (better for Docker / deployment)
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

celery_app = Celery(
    "app",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.inference_task"]  # make sure this path is correct
)

# ✅ Robust configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,

    # 🔥 Critical fixes
    broker_connection_retry_on_startup=True,   # retry if Redis not ready
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # 🔥 Prevent hanging tasks
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # 🔥 Time limits (optional but good)
    task_time_limit=300,
    task_soft_time_limit=240,
)