
import logging

from celery.exceptions import CeleryError
from fastapi import APIRouter, HTTPException, status

from app.celery_worker import celery

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def task_health():
    """Check broker connectivity and worker availability."""

    try:
        with celery.connection_for_read() as connection:
            connection.ensure_connection(
                max_retries=1,
                interval_start=0,
                interval_step=0.2,
                interval_max=0.5,
            )

        inspector = celery.control.inspect(timeout=1.5)
        workers = inspector.ping() or {}

        if not workers:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "unhealthy",
                    "broker": "connected",
                    "worker": "unavailable",
                },
            )

        return {
            "status": "healthy",
            "broker": "connected",
            "worker": "available",
            "worker_count": len(workers),
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Celery health check failed")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "message": "Celery broker or worker check failed.",
            },
        ) from exc
