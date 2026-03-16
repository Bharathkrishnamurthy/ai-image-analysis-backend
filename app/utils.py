import cv2
import numpy as np


def read_image(image_bytes: bytes):
    """
    Convert raw image bytes to OpenCV image.

    Args:
        image_bytes (bytes): Raw file bytes from UploadFile

    Returns:
        np.ndarray: Decoded image
    """import cv2
import numpy as np
import os
import uuid
from typing import List, Dict


# ==========================================================
# IMAGE PROCESSING UTILITIES
# ==========================================================

def read_image(image_bytes: bytes) -> np.ndarray:
    """
    Convert raw image bytes to OpenCV image.

    Args:
        image_bytes (bytes): Raw file bytes from UploadFile

    Returns:
        np.ndarray: Decoded OpenCV image
    """

    if not image_bytes:
        raise ValueError("Empty image data")

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Invalid image file")

    return img


def resize_image(image: np.ndarray, max_size: int = 1024) -> np.ndarray:
    """
    Resize image while maintaining aspect ratio.
    Useful for large uploads.
    """

    height, width = image.shape[:2]

    if max(height, width) <= max_size:
        return image

    scale = max_size / max(height, width)
    new_width = int(width * scale)
    new_height = int(height * scale)

    return cv2.resize(image, (new_width, new_height))


# ==========================================================
# FILE HANDLING UTILITIES
# ==========================================================

def save_uploaded_file(image_bytes: bytes, upload_dir: str = "uploads") -> str:
    """
    Save uploaded file to disk with unique filename.

    Returns:
        str: Saved filename
    """

    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    filename = f"{uuid.uuid4().hex}.jpg"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return filename


# ==========================================================
# YOLO RESULT FORMATTER
# ==========================================================

def format_yolo_results(results) -> Dict:
    """
    Convert YOLO output into clean JSON format.
    """

    detections: List[Dict] = []

    for result in results:
        for box in result.boxes:
            detections.append({
                "class_id": int(box.cls[0]),
                "confidence": float(box.conf[0]),
                "bbox": box.xyxy[0].tolist()
            })

    return {
        "total_objects": len(detections),
        "detections": detections
    }

    if not image_bytes:
        raise ValueError("Empty image data")

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Invalid image file")

    return img
