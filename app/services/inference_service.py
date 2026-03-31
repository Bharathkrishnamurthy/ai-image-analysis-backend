from app.services.yolo_service import detect_objects
from app.db.database import SessionLocal
from app.models.detection import Detection  # ✅ FIXED IMPORT

import logging
import time

logger = logging.getLogger(__name__)


def run_inference_pipeline(image_path: str, request_id: str):
    db = SessionLocal()

    try:
        logger.info(f"🚀 Starting inference for {request_id}")

        # 🔍 Get record
        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if not detection:
            logger.error(f"❌ No detection found for {request_id}")
            return

        start_time = time.time()

        # 🔥 Run YOLO
        result = detect_objects(image_path)

        end_time = time.time()

        # ✅ Normalize result
        if "error" in result:
            detection.status = "failed"
            detection.results = {
                "total_objects": 0,
                "detections": [],
                "processing_time": 0,
                "error": result["error"]
            }
        else:
            detection.status = "completed"
            detection.results = result

        db.commit()
        db.refresh(detection)

        logger.info(f"✅ Inference completed for {request_id} in {round(end_time - start_time, 3)}s")

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {str(e)}")

        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if detection:
            detection.status = "failed"
            detection.results = {
                "total_objects": 0,
                "detections": [],
                "processing_time": 0,
                "error": str(e)
            }
            db.commit()

    finally:
        db.close()