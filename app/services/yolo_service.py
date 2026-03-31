import os
import time
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")

# ✅ GLOBAL MODEL (lazy load)
model = None


def get_model():
    global model
    if model is None:
        from ultralytics import YOLO
        logger.info("🔥 Loading YOLO model...")
        model = YOLO(MODEL_PATH)
    return model


def detect_objects(image_path: str, confidence_threshold: float = 0.5):
    start_time = time.time()

    try:
        if not os.path.exists(image_path):
            return {"error": f"Image not found: {image_path}"}

        # ✅ load once
        model = get_model()

        # ✅ optimized inference
        results = model.predict(image_path, conf=confidence_threshold, verbose=False)

        detections = []

        for result in results:
            boxes = result.boxes

            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    label = model.names[class_id]
                    confidence = float(box.conf[0])

                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    detections.append({
                        "label": label,
                        "confidence": round(confidence, 2),
                        "bbox": {
                            "x1": round(x1, 2),
                            "y1": round(y1, 2),
                            "x2": round(x2, 2),
                            "y2": round(y2, 2)
                        }
                    })

        return {
            "total_objects": len(detections),
            "processing_time": round(time.time() - start_time, 3),
            "confidence_threshold": confidence_threshold,
            "detections": detections
        }

    except Exception as e:
        logger.error(f"YOLO failed: {str(e)}")

        return {
            "error": str(e),
            "total_objects": 0,
            "detections": []
        }