from ultralytics import YOLO
import time

# Load YOLOv8 model (lightweight model)
model = YOLO("yolov8n.pt")


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