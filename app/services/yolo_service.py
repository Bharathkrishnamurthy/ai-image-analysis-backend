import os
import time
import logging

from ultralytics import YOLO

logger = logging.getLogger(__name__)

# 🔥 Force local mode (IMPORTANT FIX)
os.environ["ULTRALYTICS_HUB"] = "False"

# 🔥 Model paths
FAST_MODEL_PATH = os.getenv("FAST_MODEL_PATH", "yolov8n.pt")
HEAVY_MODEL_PATH = os.getenv("MODEL_PATH", "yolov8m.pt")

fast_model = None
heavy_model = None


def load_model(model_path: str):
    """
    Load YOLO model strictly from local weights
    """
    try:
        logger.info(f"📦 Loading model from: {model_path}")

        # Ensure file exists or download automatically
        model = YOLO(model_path)

        logger.info("✅ Model loaded successfully")
        return model

    except Exception as e:
        logger.error(f"❌ Model loading failed: {str(e)}")
        raise


def get_model(mode="fast"):
    global fast_model, heavy_model

    if mode == "fast":
        if fast_model is None:
            logger.info("⚡ Initializing FAST model...")
            fast_model = load_model(FAST_MODEL_PATH)
        return fast_model

    elif mode == "heavy":
        if heavy_model is None:
            logger.info("🧠 Initializing HEAVY model...")
            heavy_model = load_model(HEAVY_MODEL_PATH)
        return heavy_model

    else:
        raise ValueError("Invalid mode. Use 'fast' or 'heavy'")


def detect_objects(image_path: str, confidence_threshold: float = 0.3, mode="fast"):
    start_time = time.time()

    try:
        # ✅ Validate input
        if not os.path.exists(image_path):
            return {"error": f"Image not found: {image_path}"}

        # ✅ Load model
        model = get_model(mode)

        # 🔥 Run prediction (strict local inference)
        results = model(image_path, conf=confidence_threshold, verbose=False)

        detections = []

        for result in results:
            boxes = result.boxes

            if boxes is None:
                continue

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
            "status": "success",
            "mode": mode,
            "total_objects": len(detections),
            "processing_time": round(time.time() - start_time, 3),
            "confidence_threshold": confidence_threshold,
            "detections": detections
        }

    except Exception as e:
        logger.exception("❌ YOLO inference failed")

        return {
            "status": "error",
            "error": str(e),
            "total_objects": 0,
            "detections": []
        }