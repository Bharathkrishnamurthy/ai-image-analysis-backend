from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.connection import get_db
from app.db.models import Detection
from app.tasks.inference_task import run_inference_task

import shutil
import os
import uuid
from datetime import datetime

router = APIRouter()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# 🚀 PREDICT (LIGHTWEIGHT NOW)
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
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # ✅ Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ✅ Store initial DB entry
        detection = Detection(
            filename=filename,
            request_id=request_id,
            image_path=file_path,
            status="queued",  # 🔥 changed
            results=None,     # 🔥 no preview now
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )

        db.add(detection)
        db.commit()
        db.refresh(detection)

        # ✅ Trigger Celery task
        try:
            run_inference_task.delay(file_path, request_id)
            celery_status = "queued"
        except Exception as e:
            print("CELERY ERROR:", e)
            celery_status = "failed_to_queue"

        return {
            "message": "Processing started 🚀",
            "request_id": request_id,
            "status": celery_status
        }

    except Exception as e:
        print("UPLOAD ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))


# 🔍 RESULT
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
                "created_at": d.created_at
            }
            for d in detections
        ]
    }