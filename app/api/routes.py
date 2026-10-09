
import logging
import os
import tempfile
import uuid
from io import BytesIO
from pathlib import Path

import cloudinary
import cloudinary.uploader
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.connection import get_db
from app.db.models import Detection
from app.tasks.inference_task import run_inference_task

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def configure_cloudinary():
    """Configure Cloudinary from environment variables."""

    cloud_name = os.getenv("CLOUD_NAME")
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")

    if not all([cloud_name, api_key, api_secret]):
        raise RuntimeError(
            "Cloudinary configuration is incomplete."
        )

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )


def validate_image(image_bytes: bytes, content_type: str):
    """Validate image size, declared MIME type, and actual image format."""

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG and PNG images are allowed.",
        )

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 5 MB.",
        )

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            expected_format = (
                "JPEG" if content_type == "image/jpeg" else "PNG"
            )

            if image.format != expected_format:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File contents do not match the image type.",
                )

            image.verify()

    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid image.",
        ) from exc

    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image is invalid or corrupted.",
        ) from exc


@router.post(
    "/predict",
    status_code=status.HTTP_202_ACCEPTED,
)
def predict_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload an image and queue YOLO inference in Celery."""

    temp_path = None

    try:
        content_type = (file.content_type or "").lower()

        # Read no more than the configured limit plus one byte.
        image_bytes = file.file.read(MAX_UPLOAD_BYTES + 1)

        validate_image(image_bytes, content_type)

        original_name = Path(file.filename or "image").name
        safe_name = original_name.replace("\x00", "")[:150]

        if not safe_name:
            safe_name = "image"

        request_id = str(uuid.uuid4())
        stored_filename = f"{request_id}_{safe_name}"

        # Cloudinary needs a temporary file for upload.
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=ALLOWED_CONTENT_TYPES[content_type],
        ) as temp_file:
            temp_file.write(image_bytes)
            temp_path = temp_file.name

        configure_cloudinary()

        upload_result = cloudinary.uploader.upload(
            temp_path,
            resource_type="image",
            folder="ai-image-analysis",
        )

        image_url = upload_result.get("secure_url")

        if not image_url:
            raise RuntimeError("Cloudinary did not return an image URL.")

        # Create the database record before queueing the task.
        detection = Detection(
            filename=stored_filename,
            request_id=request_id,
            image_path=image_url,
            status="pending",
            prediction=None,
            confidence=None,
            processing_time=None,
            model_version="yolo-v1",
            results={
                "summary": "Inference queued",
                "status": "pending",
            },
            user_id=current_user.id,
        )

        db.add(detection)
        db.commit()
        db.refresh(detection)

        # Queue only the request ID. The worker retrieves the URL
        # from this database record.
        try:
            run_inference_task.delay(request_id)

        except Exception as queue_error:
            logger.exception(
                "Could not enqueue inference for %s",
                request_id,
            )

            detection.status = "failed"
            detection.results = {
                "summary": "Could not queue inference",
                "status": "failed",
                "error": "Background processing is unavailable.",
            }
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Background processing is unavailable. Please try again later.",
            ) from queue_error

        return {
            "message": "Image uploaded; inference queued.",
            "request_id": request_id,
            "status": "pending",
            "preview": None,
            "result": {
                "summary": "Inference queued",
                "status": "pending",
            },
            "image_url": image_url,
        }

    except HTTPException:
        raise

    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database operation failed during image upload.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed.",
        ) from exc

    except Exception as exc:
        db.rollback()
        logger.exception("Image upload failed.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image upload failed. Please try again.",
        ) from exc

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                logger.warning(
                    "Could not remove upload temporary file: %s",
                    temp_path,
                )

        file.file.close()


@router.get("/result/{request_id}")
def get_result(
    request_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return the status and result of one of the current user's jobs."""

    detection = (
        db.query(Detection)
        .filter(
            Detection.request_id == request_id,
            Detection.user_id == current_user.id,
        )
        .first()
    )

    if detection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found.",
        )

    return {
        "request_id": detection.request_id,
        "status": (detection.status or "pending").lower(),
        "prediction": detection.prediction,
        "confidence": detection.confidence,
        "processing_time": detection.processing_time,
        "model_version": detection.model_version,
        "image_url": detection.image_path,
        "result": detection.results or {},
    }


@router.get("/history")
def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return paginated prediction history for the authenticated user."""

    query = db.query(Detection).filter(
        Detection.user_id == current_user.id
    )

    total = query.count()

    detections = (
        query.order_by(
            Detection.created_at.desc(),
            Detection.id.desc(),
        )
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": [
            {
                "request_id": item.request_id,
                "filename": item.filename,
                "status": (item.status or "pending").lower(),
                "prediction": item.prediction,
                "confidence": item.confidence,
                "processing_time": item.processing_time,
                "model_version": item.model_version,
                "result": item.results or {},
                "image_url": item.image_path,
                "created_at": item.created_at,
            }
            for item in detections
        ],
    }


@router.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return analytics for the authenticated user's detections."""

    detections = (
        db.query(Detection)
        .filter(Detection.user_id == current_user.id)
        .all()
    )

    total_uploads = len(detections)
    completed_jobs = 0
    failed_jobs = 0
    object_counts = {}
    processing_times = []

    for item in detections:
        item_status = (item.status or "").lower()

        if item_status == "completed":
            completed_jobs += 1
        elif item_status == "failed":
            failed_jobs += 1

        # Count objects only for successfully completed predictions.
        if item_status == "completed" and item.results:
            for label, count in item.results.get("analytics", {}).items():
                try:
                    object_counts[label] = (
                        object_counts.get(label, 0) + int(count)
                    )
                except (TypeError, ValueError):
                    logger.warning(
                        "Invalid analytics value in detection %s",
                        item.request_id,
                    )

        if item_status == "completed" and item.processing_time:
            try:
                processing_time = float(item.processing_time)
                if processing_time >= 0:
                    processing_times.append(processing_time)
            except (TypeError, ValueError):
                logger.warning(
                    "Invalid processing time in detection %s",
                    item.request_id,
                )

    most_detected_object = (
        max(object_counts, key=object_counts.get)
        if object_counts
        else None
    )

    average_processing_time = (
        round(sum(processing_times) / len(processing_times), 2)
        if processing_times
        else 0
    )

    return {
        "total_uploads": total_uploads,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "most_detected_object": most_detected_object,
        "object_counts": object_counts,
        "average_processing_time": average_processing_time,
    }
