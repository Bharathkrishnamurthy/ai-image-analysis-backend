from app.celery_worker import celery
from app.db.connection import SessionLocal
from app.db.models import Detection

import logging
import time
import traceback
import os


# ✅ Logger
logger = logging.getLogger(__name__)


@celery.task(
    bind=True,

    name="app.tasks.run_inference_task",

    autoretry_for=(Exception,),

    retry_kwargs={"max_retries": 3},

    retry_backoff=True
)
def run_inference_task(self, image_path, request_id):

    db = SessionLocal()

    detection = None

    try:

        from app.services.yolo_service import detect_objects

        logger.info(f"🚀 TASK STARTED → {request_id}")

        # ✅ Fetch detection record
        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if not detection:

            logger.error(
                f"❌ Detection record not found → {request_id}"
            )

            return {
                "status": "FAILED",
                "reason": "record_not_found"
            }

        # ✅ Skip already completed tasks
        if detection.status == "COMPLETED":

            logger.info(
                f"⏭️ Task already completed → {request_id}"
            )

            return {
                "status": "SKIPPED"
            }

        # ✅ Update processing state
        detection.status = "PROCESSING"

        db.commit()

        # ✅ Validate image exists
        if not os.path.exists(image_path):

            raise Exception(
                f"Image file not found → {image_path}"
            )

        # 🚀 Start timing
        start_time = time.time()

        # 🔥 Run YOLO Detection
        raw_result = detect_objects(image_path)

        if "error" in raw_result:

            raise Exception(raw_result["error"])

        # 🚀 End timing
        end_time = time.time()

        processing_time = round(
            end_time - start_time,
            2
        )

        detections = raw_result.get(
            "detections",
            []
        )

        # ✅ Format object list
        objects_list = [
            {
                "object": d["label"],

                "confidence": (
                    f"{round(d['confidence'] * 100, 2)}%"
                )
            }

            for d in detections
        ]

        # ✅ Object Analytics
        analytics = {}

        for d in detections:

            label = d["label"]

            analytics[label] = (
                analytics.get(label, 0) + 1
            )

        analytics = dict(
            sorted(
                analytics.items(),
                key=lambda x: x[1],
                reverse=True
            )
        )

        # ✅ Main prediction
        main_prediction = (
            objects_list[0]["object"]
            if objects_list else "unknown"
        )

        # ✅ Main confidence
        main_confidence = (
            objects_list[0]["confidence"]
            if objects_list else "0%"
        )

        # ✅ Save final structured result
        detection.results = {

            "summary": (
                f"Detected "
                f"{raw_result.get('total_objects', 0)} "
                f"object(s)"
            ),

            "total_objects": raw_result.get(
                "total_objects",
                0
            ),

            "objects": objects_list,

            "analytics": analytics,

            "processing_time": processing_time,

            "status": "success"
        }

        # ✅ Save AI metadata
        detection.prediction = main_prediction

        detection.confidence = main_confidence

        detection.processing_time = str(
            processing_time
        )

        detection.model_version = "yolo-v1"

        detection.status = "COMPLETED"

        db.commit()

        db.refresh(detection)

        logger.info(
            f"✅ TASK COMPLETED → {request_id}"
        )

        return {

            "status": "COMPLETED",

            "request_id": request_id,

            "objects_detected": len(objects_list),

            "processing_time": processing_time
        }

    except Exception as e:

        error_trace = traceback.format_exc()

        logger.error(
            f"❌ TASK FAILED → {request_id}"
        )

        logger.error(error_trace)

        # ✅ Safe DB rollback
        db.rollback()

        # ✅ Update DB failure state
        if detection:

            try:

                detection.status = "FAILED"

                detection.results = {

                    "summary": "Processing failed",

                    "error": str(e),

                    "trace": error_trace
                }

                db.commit()

            except Exception as db_error:

                logger.error(
                    f"❌ DB UPDATE FAILED → {db_error}"
                )

        return {

            "status": "FAILED",

            "error": str(e)
        }

    finally:

        db.close()