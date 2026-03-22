from ultralytics import YOLO
import os
import time
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")

print("🚀 Loading YOLO model...")
model = YOLO(MODEL_PATH)
print("✅ YOLO model loaded successfully")


def detect_objects(image_path: str):
    start_time = time.time()

    try:
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
        logger.error(f"YOLO inference failed: {str(e)}")
        return {
            "error": "Inference failed",
            "details": str(e)
        }