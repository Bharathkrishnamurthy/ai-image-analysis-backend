
import logging
import os
import tempfile
import time
from urllib.parse import urlparse

import requests
from PIL import Image
from celery.exceptions import SoftTimeLimitExceeded

from app.celery_worker import celery
from app.db.connection import SessionLocal
from app.db.models import Detection
from app.services.yolo_service import detect_objects

logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def download_cloudinary_image(image_url: str) -> str:
    """Download an application-uploaded Cloudinary image safely."""

    parsed = urlparse(image_url)

    if parsed.scheme != "https":
        raise ValueError("Image URL must use HTTPS.")

    hostname = (parsed.hostname or "").lower()

    if not (
        hostname == "cloudinary.com"
        or hostname.endswith(".cloudinary.com")
    ):
        raise ValueError("Image URL is not from Cloudinary.")

    if parsed.username or parsed.password or parsed.port:
        raise ValueError("Unexpected image URL format.")

    response = requests.get(
        image_url,
        stream=True,
        timeout=(10, 45),
        allow_redirects=False,
    )

    try:
        response.raise_for_status()

        content_type = (
            response.headers.get("Content-Type", "")
            .split(";")[0]
            .strip()
            .lower()
        )

        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError("Downloaded file is not a supported image.")

        content_length = response.headers.get("Content-Length")

        if content_length:
            try:
                if int(content_length) > MAX_IMAGE_BYTES:
                    raise ValueError("Image exceeds the allowed size.")
            except ValueError as exc:
                if str(exc) == "Image exceeds the allowed size.":
                    raise
                raise ValueError("Invalid image content length.") from exc

        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=ALLOWED_CONTENT_TYPES[content_type],
            ) as temp_file:
                temp_path = temp_file.name
                total_bytes = 0

                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue

                    total_bytes += len(chunk)

                    if total_bytes > MAX_IMAGE_BYTES:
                        raise ValueError("Image exceeds the allowed size.")

                    temp_file.write(chunk)

            if total_bytes == 0:
                raise ValueError("Downloaded image is empty.")

            # Validate that the bytes form a readable image.
            with Image.open(temp_path) as image:
                if image.format not in {"JPEG", "PNG"}:
                    raise ValueError("Only JPEG and PNG images are allowed.")
                image.verify()

            return temp_path

        except Exception:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    finally:
        response.close()


@celery.task(
    bind=True,
    name="app.tasks.run_inference_task",
    max_retries=3,
)
def run_inference_task(self, request_id: str):
    db = SessionLocal()
    temp_path = None

    try:
        detection = (
            db.query(Detection)
            .filter(Detection.request_id == request_id)
            .first()
        )

        if detection is None:
            logger.error("Detection record not found: %s", request_id)
            return {
                "request_id": request_id,
                "status": "failed",
                "reason": "record_not_found",
            }

        current_status = (detection.status or "").lower()

        if current_status == "completed":
            return {
                "request_id": request_id,
                "status": "completed",
                "message": "Already processed",
            }

        if not detection.image_path:
            raise ValueError("Detection record has no image URL.")

        image_url = detection.image_path

        detection.status = "processing"
        detection.results = {
            "summary": "Inference is in progress",
            "status": "processing",
        }
        db.commit()

        temp_path = download_cloudinary_image(image_url)

        start_time = time.perf_counter()

        raw_result = detect_objects(
            temp_path,
            confidence_threshold=0.25,
        )

        processing_time = round(
            time.perf_counter() - start_time,
            2,
        )

        if not isinstance(raw_result, dict):
            raise RuntimeError("YOLO returned an invalid result.")

        if raw_result.get("error"):
            raise RuntimeError(str(raw_result["error"]))

        raw_detections = raw_result.get("detections", [])

        objects_list = []
        analytics = {}

        for item in raw_detections:
            label = str(item["label"])
            confidence = float(item["confidence"])

            if not 0 <= confidence <= 1:
                raise ValueError("YOLO returned an invalid confidence.")

            objects_list.append({
                "object": label,
                "confidence": f"{round(confidence * 100, 2)}%",
            })

            analytics[label] = analytics.get(label, 0) + 1

        analytics = dict(
            sorted(
                analytics.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

        total_objects = len(objects_list)

        final_result = {
            "summary": f"Detected {total_objects} object(s)",
            "total_objects": total_objects,
            "objects": objects_list,
            "analytics": analytics,
            "processing_time": processing_time,
            "status": "success",
        }

        # Re-fetch the record after inference before updating it.
        detection = (
            db.query(Detection)
            .filter(Detection.request_id == request_id)
            .first()
        )

        if detection is None:
            raise RuntimeError("Detection record disappeared.")

        detection.prediction = (
            objects_list[0]["object"] if objects_list else "unknown"
        )
        detection.confidence = (
            objects_list[0]["confidence"] if objects_list else "0%"
        )
        detection.processing_time = str(processing_time)
        detection.results = final_result
        detection.status = "completed"

        db.commit()

        logger.info("Inference completed: %s", request_id)

        return {
            "request_id": request_id,
            "status": "completed",
            "objects_detected": total_objects,
            "processing_time": processing_time,
        }

    except Exception as exc:
        db.rollback()

        logger.exception(
            "Inference attempt failed for request %s",
            request_id,
        )

        # Retry transient failures. Do not mark the request failed
        # until all configured attempts have been exhausted.
        if self.request.retries < self.max_retries:
            try:
                detection = (
                    db.query(Detection)
                    .filter(Detection.request_id == request_id)
                    .first()
                )

                if detection is not None:
                    detection.status = "pending"
                    detection.results = {
                        "summary": "Inference retry scheduled",
                        "status": "pending",
                    }
                    db.commit()

            except Exception:
                db.rollback()
                logger.exception("Could not update retry status.")

            raise self.retry(
                exc=exc,
                countdown=2 ** (self.request.retries + 1),
            )

        # All attempts exhausted.
        try:
            detection = (
                db.query(Detection)
                .filter(Detection.request_id == request_id)
                .first()
            )

            if detection is not None:
                detection.status = "failed"
                detection.results = {
                    "summary": "Processing failed",
                    "status": "failed",
                    "error": "Inference failed after retries.",
                }
                db.commit()

        except Exception:
            db.rollback()
            logger.exception("Could not save final failure status.")

        return {
            "request_id": request_id,
            "status": "failed",
            "error": "Inference failed after retries.",
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                logger.warning(
                    "Could not remove temporary image: %s",
                    temp_path,
                )

        db.close()
