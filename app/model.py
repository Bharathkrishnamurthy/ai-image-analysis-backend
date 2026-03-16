from ultralytics import YOLO
import time
import os

# ---------------------------------------------------
# Load YOLO model only once (important for performance)
# ---------------------------------------------------
MODEL_PATH = "yolov8n.pt"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

model = YOLO(MODEL_PATH)


def detect_objects(image_path: str, confidence_threshold: float = 0.5) -> dict:
    """
    Runs YOLO object detection on an image.

    Args:
        image_path (str): Path to uploaded image
        confidence_threshold (float): Minimum confidence to keep detection

    Returns:
        dict: Structured detection results
    """

    try:
        if not os.path.exists(image_path):
            return {"error": f"Image not found: {image_path}"}

        start_time = time.time()

        # Run inference
        results = model(image_path)

        end_time = time.time()
        processing_time = round(end_time - start_time, 3)

        detections = []

        # Extract detections
        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = model.names.get(cls_id, "unknown")

                if conf >= confidence_threshold:
                    detections.append({
                        "class": class_name,
                        "confidence": round(conf, 2)
                    })

        return {
            "total_objects": len(detections),
            "processing_time_seconds": processing_time,
            "confidence_threshold": confidence_threshold,
            "detections": detections
        }

    except Exception as e:
        return {
            "error": str(e)
        }
