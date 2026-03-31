from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def task_health():
    return {"status": "Celery routes working"}