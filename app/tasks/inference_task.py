from app.celery_worker import celery_app
from app.db.connection import SessionLocal
from app.db.models import Detection

import logging
import time

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.inference_task.run_inference_task")
def run_inference_task(file_path, request_id):
    db = SessionLocal()

    try:
        from app.services.yolo_service import detect_objects

        logger.info(f"🔥 TASK STARTED: {request_id}")

        start_time = time.time()

        result = detect_objects(file_path)

        end_time = time.time()

        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if not detection:
            logger.error(f"❌ No record found for {request_id}")
            return

        detection.results = {
            "total_objects": len(result),
            "objects": result,
            "processing_time": round(end_time - start_time, 3)
        }

        detection.status = "completed"

        db.commit()
        db.refresh(detection)

        logger.info(f"✅ Detection completed for {request_id}")

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")

        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if detection:
            detection.status = "failed"
            detection.results = {
                "total_objects": 0,
                "objects": [],
                "processing_time": 0,
                "error": str(e)
            }
            db.commit()

    finally:
        db.close()