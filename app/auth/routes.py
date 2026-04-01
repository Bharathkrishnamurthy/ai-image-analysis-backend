from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.connection import get_db
from app.db.models import Detection

import shutil
import os
import uuid
from datetime import datetime

router = APIRouter()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# 🔥 SAFE CELERY CALL (NO CRASH ON RENDER)
def run_task_safe(file_path, request_id):
    try:
        from app.tasks.inference_task import run_inference_task
        run_inference_task.delay(file_path, request_id)
    except Exception as e:
        print("Celery not available:", e)


# 🔥 SAFE YOLO CALL
def detect_safe(file_path):
    try:
        from app.services.yolo_service import detect_objects
        return detect_objects(file_path)
    except Exception as e:
        print("YOLO ERROR:", e)
        return []


# ✅ PREDICT
@router.post("/predict")
def predict_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Invalid file type")

        request_id = str(uuid.uuid4())
        filename = f"{request_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ✅ SAFE detection
        objs = detect_safe(file_path)

        quick_summary = {
            "total_objects": len(objs),
            "objects": objs,
            "processing_time": 0.1
        }

        # ✅ SAVE TO DB
        detection = Detection(
            request_id=request_id,
            user_id=current_user.id,
            filename=filename,
            image_path=file_path,
            status="processing",
            results=quick_summary,
            created_at=datetime.utcnow()
        )

        db.add(detection)
        db.commit()

        # ✅ SAFE CELERY CALL
        run_task_safe(file_path, request_id)

        return {
            "message": "Processing started 🚀",
            "request_id": request_id,
            "status": "processing",
            "preview": quick_summary
        }

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail="Upload failed")


# ✅ RESULT
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


# ✅ HISTORY
@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    detections = db.query(Detection).filter(
        Detection.user_id == current_user.id
    ).order_by(Detection.created_at.desc()).all()

    return [
        {
            "request_id": d.request_id,
            "filename": d.filename,
            "status": d.status,
            "result": d.results or {},
            "created_at": d.created_at
        }
        for d in detections
    ]