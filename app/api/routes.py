from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    Query
)

from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.connection import get_db
from app.db.models import Detection
from app.tasks.inference_task import run_inference_task
from app.services.yolo_service import detect_objects

import cloudinary
import cloudinary.uploader

import os
import uuid
import tempfile
import shutil

from datetime import datetime

router = APIRouter()


# 🔥 Configure Cloudinary
def configure_cloudinary():
    cloudinary.config(
        cloud_name=os.getenv("CLOUD_NAME"),
        api_key=os.getenv("API_KEY"),
        api_secret=os.getenv("API_SECRET")
    )


# 🔥 Toggle Celery Background Tasks
USE_BACKGROUND_TASK = False


# 🚀 IMAGE PREDICTION
@router.post("/predict")
def predict_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    temp_path = None

    try:
        # ✅ Configure cloudinary
        configure_cloudinary()

        # ✅ Validate file type
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(
                status_code=400,
                detail="Only JPG and PNG images are allowed"
            )

        # ✅ Validate file size (5MB)
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File too large (max 5MB)"
            )

        # ✅ Generate IDs
        filename = f"{uuid.uuid4()}_{file.filename}"
        request_id = str(uuid.uuid4())

        # ✅ Save temporary file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jpg"
        )

        shutil.copyfileobj(file.file, temp_file)

        temp_file.close()

        temp_path = temp_file.name

        # 🔥 Upload image to Cloudinary
        upload_result = cloudinary.uploader.upload(temp_path)

        image_url = upload_result.get("secure_url")

        if not image_url:
            raise HTTPException(
                status_code=500,
                detail="Cloudinary upload failed"
            )

        # 🔥 YOLO Detection
        full_result = detect_objects(
            temp_path,
            confidence_threshold=0.25
        )

        if "error" in full_result:
            raise Exception(full_result["error"])

        # ✅ Format object list
        objects_list = [
            {
                "object": d["label"],
                "confidence": f"{round(d['confidence'] * 100, 2)}%"
            }
            for d in full_result.get("detections", [])
        ]

        # ✅ Analytics
        analytics = {}

        for d in full_result.get("detections", []):

            label = d["label"]

            analytics[label] = analytics.get(label, 0) + 1

        analytics = dict(
            sorted(
                analytics.items(),
                key=lambda x: x[1],
                reverse=True
            )
        )

        # ✅ Final AI Result
        final_result = {
            "summary": f"Detected {full_result.get('total_objects', 0)} object(s)",
            "total_objects": full_result.get("total_objects", 0),
            "objects": objects_list,
            "analytics": analytics,
            "processing_time": full_result.get("processing_time"),
            "status": "success"
        }

        # ✅ Save Detection to PostgreSQL
        detection = Detection(

            filename=filename,

            request_id=request_id,

            image_path=image_url,

            status="completed",

            prediction=(
                objects_list[0]["object"]
                if objects_list else "unknown"
            ),

            confidence=(
                objects_list[0]["confidence"]
                if objects_list else "0%"
            ),

            processing_time=str(
                full_result.get("processing_time")
            ),

            model_version="yolo-v1",

            results=final_result,

            user_id=current_user.id,

            created_at=datetime.utcnow()
        )

        db.add(detection)

        db.commit()

        db.refresh(detection)

        # 🔥 Optional Celery Background Processing
        if USE_BACKGROUND_TASK:
            run_inference_task.delay(
                image_url,
                request_id
            )

        # ✅ API Response
        return {
            "message": "Processing completed 🚀",

            "request_id": request_id,

            "status": "completed",

            "preview": {
                "total_objects": final_result["total_objects"],
                "objects": final_result["objects"]
            },

            "result": final_result,

            "image_url": image_url
        }

    except Exception as e:

        print("UPLOAD ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


# 🔍 GET SINGLE RESULT
@router.get("/result/{request_id}")
def get_result(
    request_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    detection = db.query(Detection).filter(
        Detection.request_id == request_id,
        Detection.user_id == current_user.id
    ).first()

    if not detection:
        raise HTTPException(
            status_code=404,
            detail="Detection not found"
        )

    return {
        "request_id": detection.request_id,

        "status": detection.status,

        "prediction": detection.prediction,

        "confidence": detection.confidence,

        "processing_time": detection.processing_time,

        "model_version": detection.model_version,

        "result": detection.results or {}
    }


# 📊 HISTORY API WITH PAGINATION
@router.get("/history")
def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),

    db: Session = Depends(get_db),

    current_user=Depends(get_current_user)
):

    offset = (page - 1) * limit

    detections = (
        db.query(Detection)
        .filter(Detection.user_id == current_user.id)
        .order_by(Detection.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    total = (
        db.query(Detection)
        .filter(Detection.user_id == current_user.id)
        .count()
    )

    return {

        "page": page,

        "limit": limit,

        "total": total,

        "data": [
            {
                "request_id": d.request_id,

                "filename": d.filename,

                "status": d.status,

                "prediction": d.prediction,

                "confidence": d.confidence,

                "processing_time": d.processing_time,

                "model_version": d.model_version,

                "result": d.results or {},

                "image_url": d.image_path,

                "created_at": d.created_at
            }

            for d in detections
        ]
    }


# 📈 ANALYTICS API
@router.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    detections = db.query(Detection).filter(
        Detection.user_id == current_user.id
    ).all()

    total_uploads = len(detections)

    completed_jobs = len([
        d for d in detections
        if d.status == "completed"
    ])

    failed_jobs = len([
        d for d in detections
        if d.status == "failed"
    ])

    object_counts = {}

    processing_times = []

    for d in detections:

        # ✅ Object analytics
        if d.results and "analytics" in d.results:

            for obj, count in d.results["analytics"].items():

                object_counts[obj] = (
                    object_counts.get(obj, 0) + count
                )

        # ✅ Processing time analytics
        if d.processing_time:

            try:
                processing_times.append(
                    float(d.processing_time)
                )

            except:
                pass

    # ✅ Average processing time
    avg_processing_time = (
        round(
            sum(processing_times) / len(processing_times),
            2
        )
        if processing_times else 0
    )

    # ✅ Most detected object
    most_detected_object = (
        max(object_counts, key=object_counts.get)
        if object_counts else None
    )

    return {

        "total_uploads": total_uploads,

        "completed_jobs": completed_jobs,

        "failed_jobs": failed_jobs,

        "most_detected_object": most_detected_object,

        "object_counts": object_counts,

        "average_processing_time": avg_processing_time
    }