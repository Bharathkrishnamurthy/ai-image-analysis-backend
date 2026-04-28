from app.celery_worker import celery_app
from app.db.connection import SessionLocal
from app.db.models import Detection

import logging
import time
import traceback
import os

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.run_inference_task"
)
def run_inference_task(self, image_path, request_id):
    db = SessionLocal()
    detection = None

    try:
        from app.services.yolo_service import detect_objects

        logger.info(f"🚀 TASK STARTED: {request_id}")

        # ✅ Fetch DB record
        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if not detection:
            logger.error(f"❌ No DB record found: {request_id}")
            return {"status": "failed", "reason": "record not found"}

        # 🔥 Skip if already done
        if detection.status == "completed":
            logger.info(f"⏭️ Already completed: {request_id}")
            return {"status": "skipped"}

        # ✅ Mark processing
        detection.status = "processing"
        db.commit()

        # ✅ Validate file exists
        if not os.path.exists(image_path):
            raise Exception(f"Image not found: {image_path}")

        start_time = time.time()

        # 🔥 LOCAL YOLO ONLY (NO API)
        raw_result = detect_objects(image_path)

        if "error" in raw_result:
            raise Exception(raw_result["error"])

        end_time = time.time()

        detections = raw_result.get("detections", [])

        # ✅ Format objects
        objects_list = [
            {
                "object": d["label"],
                "confidence": f"{round(d['confidence'] * 100, 2)}%"
            }
            for d in detections
        ]

        # ✅ Analytics
        analytics = {}
        for d in detections:
            label = d["label"]
            analytics[label] = analytics.get(label, 0) + 1

        analytics = dict(sorted(analytics.items(), key=lambda x: x[1], reverse=True))

        # ✅ Save results
        detection.results = {
            "summary": f"Detected {raw_result.get('total_objects', 0)} object(s)",
            "total_objects": raw_result.get("total_objects", 0),
            "objects": objects_list,
            "analytics": analytics,
            "processing_time": f"{round(end_time - start_time, 2)} seconds",
            "status": "success"
        }

        detection.status = "completed"
        db.commit()
        db.refresh(detection)

        logger.info(f"✅ TASK COMPLETED: {request_id}")

        return {
            "status": "completed",
            "objects": len(objects_list)
        }

    except Exception as e:
        error_trace = traceback.format_exc()

        logger.error(f"❌ TASK FAILED: {request_id}")
        logger.error(error_trace)

        if detection:
            try:
                detection.status = "failed"
                detection.results = {
                    "summary": "Processing failed",
                    "error": str(e),
                    "trace": error_trace
                }
                db.commit()
            except Exception as db_error:
                logger.error(f"❌ DB UPDATE FAILED: {db_error}")

        return {
            "status": "failed",
            "error": str(e)
        }

    finally:
        db.close()