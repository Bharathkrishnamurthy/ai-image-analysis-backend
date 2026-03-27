from celery import Celery

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# ✅ Queue routing
celery_app.conf.task_routes = {
    "app.tasks.inference_task.run_inference_task": {"queue": "inference"}
}

# ✅ IMPORTANT: Serialization + timezone
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# ✅ IMPORTANT: Auto-discover tasks