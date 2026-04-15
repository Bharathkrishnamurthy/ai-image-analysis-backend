from app.celery_worker import celery_app
from app.db.connection import SessionLocal
from app.db.models import Detection

import logging
import time
import traceback
import requests
import tempfile
import os

logger = logging.getLogger(__name__)


# ✅ Download image from URL (Cloudinary)
def download_image(url):
    response = requests.get(url, timeout=30)  # 🔥 add timeout
    response.raise_for_status()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_file.write(response.content)
    temp_file.close()

    return temp_file.name


@celery_app.task(
    bind=True,
    name="app.tasks.inference_task.run_inference_task",
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3}
)
def run_inference_task(self, image_url, request_id):
    db = SessionLocal()
    detection = None
    local_path = None

    try:
        from app.services.yolo_service import detect_objects

        logger.info(f"🔥 TASK STARTED: {request_id}")
        logger.info(f"🌐 IMAGE URL: {image_url}")

        # ✅ STEP 1: Download image
        local_path = download_image(image_url)
        logger.info(f"📥 Image downloaded to: {local_path}")

        start_time = time.time()

        # ✅ STEP 2: Run YOLO
        raw_result = detect_objects(local_path)

        # 🔥 HANDLE ERROR CASE
        if "error" in raw_result:
            raise Exception(raw_result["error"])

        logger.info(f"🧠 RAW YOLO OUTPUT: {raw_result}")

        end_time = time.time()

        # ✅ STEP 3: Fetch DB record
        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if not detection:
            logger.error(f"❌ No DB record found for request_id: {request_id}")
            return

        # ✅ Extract detections
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

        # ✅ Save result
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
        # 🔥 CLEANUP TEMP FILE
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"🧹 Temp file deleted: {local_path}")

        db.close()