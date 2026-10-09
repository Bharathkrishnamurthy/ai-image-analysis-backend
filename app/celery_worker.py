
import os
import ssl

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError(
        "REDIS_URL is missing from environment variables."
    )

# Enable TLS automatically for Upstash Redis.
if REDIS_URL.startswith("redis://") and "upstash.io" in REDIS_URL:
    REDIS_URL = "rediss://" + REDIS_URL[len("redis://"):]

celery = Celery(
    "ai_image_analysis",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.inference_task"],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    timezone="Asia/Kolkata",
    enable_utc=True,

    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    task_time_limit=300,
    task_soft_time_limit=240,

    worker_concurrency=1,
    task_default_queue="celery",
    task_track_started=True,

    result_expires=3600,
)

# Configure TLS only when the connection actually uses rediss://.
if REDIS_URL.startswith("rediss://"):
    celery.conf.update(
        broker_use_ssl={
            "ssl_cert_reqs": ssl.CERT_REQUIRED,
        },
        redis_backend_use_ssl={
            "ssl_cert_reqs": ssl.CERT_REQUIRED,
        },
    )
