from app.services.yolo_service import detect_objects
from app.db.database import SessionLocal
from app.models.result import Result
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


def run_inference_pipeline(image_path: str, user_id: int, filename: str):
    db = SessionLocal()

    # 🔥 Generate job ID (important for tracking)
    request_id = str(uuid.uuid4())

    try:
        # ✅ Step 0: Create initial DB entry (status = processing)
        db_result = Result(
            user_id=user_id,
            image_path=image_path,
            filename=filename,
            request_id=request_id,
            status="processing",
            created_at=datetime.utcnow()
        )

        db.add(db_result)
        db.commit()
        db.refresh(db_result)

        # 🔥 Step 1: Run YOLO
        result = detect_objects(image_path)

        # 🔥 Step 2: Update DB with results
        db_result.output = result
        db_result.status = "completed"

        db.commit()

        logger.info(f"✅ Inference completed for {filename}")

    except Exception as e:
        # ❌ Update DB with failure
        db_result.status = "failed"
        db_result.output = {"error": str(e)}

        db.commit()

        logger.error(f"❌ Pipeline failed: {str(e)}")

    finally:
        db.close()