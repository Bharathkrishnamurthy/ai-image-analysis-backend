from app.celery_worker import celery_app
from app.db.connection import SessionLocal
from app.db.models import Detection

import logging

logger = logging.getLogger(__name__)


@celery_app.task
def run_inference_task(file_path, request_id):
    db = SessionLocal()

    try:
        # ✅ IMPORT INSIDE TASK (CRITICAL FIX)
        from app.services.yolo_service import detect_objects

        # 🔥 Run YOLO
        result = detect_objects(file_path)

        # 🔍 Fetch record
        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if not detection:
            logger.error(f"❌ No record found for {request_id}")
            return

        # ✅ Update DB
        detection.results = result
        detection.status = "completed"

        db.commit()

        logger.info(f"✅ Detection completed: {request_id}")

    except Exception as e:
        logger.error(f"❌ Inference failed: {str(e)}")

        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if detection:
            detection.status = "failed"
            detection.results = {"error": str(e)}
            db.commit()

    finally:
        db.close()