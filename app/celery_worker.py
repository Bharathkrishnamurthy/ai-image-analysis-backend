from celery import Celery
import os

# ✅ Get Redis URL
REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise ValueError("❌ REDIS_URL is not set in environment variables")

# ✅ Force secure connection (Upstash requires TLS)
if REDIS_URL.startswith("redis://"):
    REDIS_URL = REDIS_URL.replace("redis://", "rediss://")

celery_app = Celery(
    "app",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.inference_task"]
)

# ✅ SSL config (IMPORTANT for Upstash)
celery_app.conf.broker_use_ssl = {"ssl_cert_reqs": "none"}
celery_app.conf.redis_backend_use_ssl = {"ssl_cert_reqs": "none"}

# ✅ FINAL CONFIG (queue + stability)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,

    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    task_acks_late=True,
    worker_prefetch_multiplier=1,

    task_time_limit=300,
    task_soft_time_limit=240,

    worker_concurrency=1,

    # 🔥 CRITICAL FIX (queue issue)
    task_default_queue="celery",
)