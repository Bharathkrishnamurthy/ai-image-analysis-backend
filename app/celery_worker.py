from celery import Celery
import os

from dotenv import load_dotenv

# 🔥 Load environment variables
load_dotenv()

# ✅ Get Redis URL
REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise ValueError(
        "❌ REDIS_URL is missing in environment variables"
    )

# ✅ Force TLS for Upstash Redis
if REDIS_URL.startswith("redis://"):
    REDIS_URL = REDIS_URL.replace(
        "redis://",
        "rediss://"
    )

# 🚀 Create Celery App
celery = Celery(
    "ai_image_analysis",

    broker=REDIS_URL,

    backend=REDIS_URL
)

# ✅ Auto discover task files
celery.autodiscover_tasks([
    "app.tasks"
])

# 🔥 SSL Config (Required for Upstash)
celery.conf.broker_use_ssl = {
    "ssl_cert_reqs": "none"
}

celery.conf.redis_backend_use_ssl = {
    "ssl_cert_reqs": "none"
}

# 🚀 Production Config
celery.conf.update(

    # ✅ Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # ✅ Timezone
    timezone="Asia/Kolkata",
    enable_utc=True,

    # ✅ Retry Handling
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # ✅ Worker Optimization
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # ✅ Task Limits
    task_time_limit=300,
    task_soft_time_limit=240,

    # ✅ Worker Scaling
    worker_concurrency=1,

    # ✅ Default Queue
    task_default_queue="celery",

    # ✅ Task Tracking
    task_track_started=True,

    # ✅ Result Expiry
    result_expires=3600
)

print("✅ Celery connected successfully")