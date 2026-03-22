from app.services.yolo_service import detect_objects
from app.db.database import SessionLocal
from app.db.models import Detection   # ✅ FIXED import
import logging
import uuid

logger = logging.getLogger(__name__)


def run_inference_pipeline(image_path: str, user_id: int, filename: str):
    db = SessionLocal()

    # 🔥 Generate job ID
    request_id = str(uuid.uuid4())

    detection = None  # for safe exception handling

    try:
        # ✅ Step 1: Create initial DB entry (processing)
        detection = Detection(
            filename=filename,
            user_id=user_id,
            request_id=request_id,
            status="processing"
        )

        db.add(detection)
        db.commit()
        db.refresh(detection)

        # 🔥 Step 2: Run YOLO
        result = detect_objects(image_path)

        # 🔥 Step 3: Update result
        detection.results = result
        detection.status = "completed"

        db.commit()

        logger.info(f"✅ Inference completed for {filename}")

    except Exception as e:
        # ❌ Handle failure safely
        if detection:
            detection.status = "failed"
            detection.results = {"error": str(e)}
            db.commit()

        logger.error(f"❌ Pipeline failed: {str(e)}")

    finally:
        db.close()