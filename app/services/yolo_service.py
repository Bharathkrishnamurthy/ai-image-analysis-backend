from ultralytics import YOLO
import os
import time

# Get model path from environment variable
MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")

print("🚀 Loading YOLO model...")

# Load model only once when service starts
model = YOLO(MODEL_PATH)

print("✅ YOLO model loaded successfully")


def detect_objects(image_path):
    start_time = time.time()

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

    end_time = time.time()

    return {
        "total_objects": len(detections),
        "objects": detections,
        "processing_time_seconds": round(end_time - start_time, 3)
    }