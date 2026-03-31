from ultralytics import YOLO
import time
import os

MODEL_PATH = "yolov8n.pt"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

model = YOLO(MODEL_PATH)


def detect_objects(image_path: str, confidence_threshold: float = 0.5) -> dict:
    try:
        if not os.path.exists(image_path):
            return {"error": f"Image not found: {image_path}"}

        start_time = time.time()

        # ✅ Optimized inference
        results = model.predict(image_path, conf=confidence_threshold, verbose=False)

        end_time = time.time()
        processing_time = round(end_time - start_time, 3)

        detections = []

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = model.names.get(cls_id, "unknown")

                x1, y1, x2, y2 = box.xyxy[0].tolist()

                detections.append({
                    "class": class_name,
                    "confidence": round(conf, 2),
                    "bbox": {
                        "x1": round(x1, 2),
                        "y1": round(y1, 2),
                        "x2": round(x2, 2),
                        "y2": round(y2, 2)
                    }
                })

        return {
            "total_objects": len(detections),
            "processing_time": processing_time,
            "confidence_threshold": confidence_threshold,
            "detections": detections
        }

    except Exception as e:
        return {
            "error": str(e),
            "total_objects": 0,
            "detections": []
        }