from app.services.yolo_service import detect_objects
from app.db.connection import SessionLocal
from app.db.models import Detection

import logging
import time

logger = logging.getLogger(__name__)


def run_inference_pipeline(image_path: str, request_id: str):
    db = SessionLocal()

    try:
        logger.info(f"🚀 Starting inference for {request_id}")

        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if not detection:
            logger.error(f"❌ No detection found for {request_id}")
            return

        start_time = time.time()

        # 🔥 Run YOLO
        raw_result = detect_objects(image_path)

        end_time = time.time()

        # ✅ Convert to simple user-friendly format
        objects_list = []
        for obj in raw_result:
            objects_list.append({
                "object": obj.get("label", "unknown"),
                "confidence": f"{round(obj.get('confidence', 0) * 100, 2)}%"
            })

        detection.status = "completed"
        detection.results = {
            "summary": f"Detected {len(objects_list)} object(s) in the image",
            "total_objects": len(objects_list),
            "objects": objects_list,
            "processing_time": f"{round(end_time - start_time, 2)} seconds"
        }

        db.commit()
        db.refresh(detection)

        logger.info(f"✅ Inference completed for {request_id}")

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {str(e)}")

        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if detection:
            detection.status = "failed"
            detection.results = {
                "summary": "Processing failed",
                "error": str(e)
            }
            db.commit()

    finally:
        db.close()