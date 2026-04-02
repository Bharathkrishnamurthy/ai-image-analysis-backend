from app.celery_worker import celery_app
from app.db.connection import SessionLocal
from app.db.models import Detection

import logging
import time
import traceback

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 3})
def run_inference_task(self, file_path, request_id):
    db = SessionLocal()

    detection = None

    try:
        from app.services.yolo_service import detect_objects

        logger.info(f"🔥 TASK STARTED: {request_id}")

        start_time = time.time()

        raw_result = detect_objects(file_path)

        logger.info(f"🧠 RAW YOLO OUTPUT: {raw_result}")

        end_time = time.time()

        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if not detection:
            logger.error(f"❌ No DB record found for request_id: {request_id}")
            return

        # ✅ Extract detections
        detections = raw_result.get("detections", [])

        # ✅ Objects list
        objects_list = [
            {
                "object": d["label"],
                "confidence": f"{round(d['confidence'] * 100, 2)}%",
                "bbox": d.get("bbox")
            }
            for d in detections
        ]

        # 🔥 NEW: Analytics grouping
        analytics = {}
        for d in detections:
            label = d["label"]
            analytics[label] = analytics.get(label, 0) + 1

        # (optional sort)
        analytics = dict(sorted(analytics.items(), key=lambda x: x[1], reverse=True))

        # ✅ Final result
        detection.results = {
            "summary": f"Detected {raw_result.get('total_objects', 0)} object(s)",
            "total_objects": raw_result.get("total_objects", 0),
            "objects": objects_list,
            "analytics": analytics,  # 🔥 NEW FIELD
            "processing_time": f"{round(end_time - start_time, 2)} seconds",
            "status": "success"
        }

        detection.status = "completed"

        db.commit()
        db.refresh(detection)

        logger.info(f"✅ Detection completed: {request_id}")

        return {"status": "completed", "objects": len(objects_list)}

    except Exception as e:
        error_trace = traceback.format_exc()

        logger.error(f"❌ TASK FAILED: {request_id}")
        logger.error(error_trace)

        try:
            if not detection:
                detection = db.query(Detection).filter(
                    Detection.request_id == request_id
                ).first()

            if detection:
                detection.status = "failed"
                detection.results = {
                    "summary": "Processing failed",
                    "error": str(e),
                    "trace": error_trace
                }
                db.commit()

        except Exception as db_error:
            logger.error(f"❌ DB UPDATE FAILED: {db_error}")

        raise self.retry(exc=e)

    finally:
        db.close()