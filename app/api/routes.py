from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.connection import get_db
from app.db.models import Detection
from app.tasks.inference_task import run_inference_task

import cloudinary
import cloudinary.uploader
import os
import uuid
from datetime import datetime

router = APIRouter()

# ✅ Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)


# 🚀 PREDICT (WITH PREVIEW)
@router.post("/predict")
def predict_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Invalid file type")

        filename = f"{uuid.uuid4()}_{file.filename}"
        request_id = str(uuid.uuid4())

        # ✅ Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(file.file)
        image_url = upload_result.get("secure_url")

        if not image_url:
            raise HTTPException(status_code=500, detail="Cloud upload failed")

        # 🔥 OPTIONAL PREVIEW (light detection)
        preview_result = {
            "message": "Preview unavailable (processed asynchronously)"
        }

        # ✅ Store DB entry
        detection = Detection(
            filename=filename,
            request_id=request_id,
            image_path=image_url,
            status="queued",
            results=None,
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )

        db.add(detection)
        db.commit()
        db.refresh(detection)

        # ✅ Trigger Celery
        run_inference_task.delay(image_url, request_id)

        return {
            "message": "Processing started 🚀",
            "request_id": request_id,
            "status": "queued",
            "preview": preview_result,
            "image_url": image_url
        }

    except Exception as e:
        print("UPLOAD ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))


# 🔍 RESULT (FULL OUTPUT)
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
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "request_id": detection.request_id,
        "status": detection.status,
        "result": detection.results or {}
    }


# 📊 HISTORY
@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    detections = db.query(Detection).filter(
        Detection.user_id == current_user.id
    ).order_by(Detection.created_at.desc()).all()

    return {
        "count": len(detections),
        "data": [
            {
                "request_id": d.request_id,
                "filename": d.filename,
                "status": d.status,
                "result": d.results or {},
                "image_url": d.image_path,
                "created_at": d.created_at
            }
            for d in detections
        ]
    }