import os
import time
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")


def detect_objects(image_path: str):
    start_time = time.time()

    try:
        # ✅ IMPORT + LOAD INSIDE FUNCTION (CRITICAL FIX)
        from ultralytics import YOLO

        model = YOLO(MODEL_PATH)

        results = model(image_path)

        detections = []

        for result in results:
            boxes = result.boxes

            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    label = model.names[class_id]
                    confidence = float(box.conf[0])

                    detections.append({
                        "label": label,
                        "confidence": round(confidence, 2)
                    })

        return {
            "total_objects": len(detections),
            "objects": detections,
            "processing_time_seconds": round(time.time() - start_time, 3)
        }

    except Exception as e:
        logger.error(f"YOLO failed: {str(e)}")
        return {"error": str(e)}