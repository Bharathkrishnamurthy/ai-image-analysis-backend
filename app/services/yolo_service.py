import os
import time
import logging

logger = logging.getLogger(__name__)

# 🔥 Two models (fast + accurate)
FAST_MODEL_PATH = os.getenv("FAST_MODEL_PATH", "yolov8n.pt")
HEAVY_MODEL_PATH = os.getenv("MODEL_PATH", "yolov8m.pt")

fast_model = None
heavy_model = None


def get_model(mode="fast"):
    global fast_model, heavy_model

    from ultralytics import YOLO

    if mode == "fast":
        if fast_model is None:
            logger.info("⚡ Loading FAST YOLO model...")
            fast_model = YOLO(FAST_MODEL_PATH)
        return fast_model

    else:
        if heavy_model is None:
            logger.info("🧠 Loading HEAVY YOLO model...")
            heavy_model = YOLO(HEAVY_MODEL_PATH)
        return heavy_model


def detect_objects(image_path: str, confidence_threshold: float = 0.3, mode="fast"):
    start_time = time.time()

    try:
        if not os.path.exists(image_path):
            return {"error": f"Image not found: {image_path}"}

        model = get_model(mode)

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