from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.connection import get_db
from app.db.models import Detection
from app.tasks.inference_task import run_inference_task
from app.services.yolo_service import detect_objects

import shutil
import os
import uuid
from datetime import datetime

router = APIRouter()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# 🚀 PREDICT (HYBRID: instant + async)
@router.post("/predict")
def predict_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        # ✅ Validate file
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Invalid file type")

        # ✅ Safe filename
        safe_name = file.filename.replace(" ", "_")
        filename = f"{uuid.uuid4()}_{safe_name}"
        request_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # ✅ Save file
        try:
            file.file.seek(0)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception:
            raise HTTPException(status_code=500, detail="File save failed")

        # ⚡ Quick detection
        try:
            quick_result = detect_objects(file_path)
        except Exception:
            quick_result = {
                "total_objects": 0,
                "objects": [],
                "processing_time_seconds": 0
            }

        # ✅ Create DB entry
        detection = Detection(
            filename=filename,
            request_id=request_id,
            status="processing",
            results=None,
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )

        db.add(detection)
        db.commit()
        db.refresh(detection)  # 🔥 IMPORTANT FIX

        # 🔄 Background task
        try:
            run_inference_task.delay(file_path, request_id)
        except Exception:
            detection.status = "failed"
            db.commit()

        return {
            "message": "Processing started 🚀",
            "request_id": request_id,
            "status": detection.status,
            "summary": {
                "total_objects": quick_result.get("total_objects", 0),
                "objects": [obj.get("label") for obj in quick_result.get("objects", [])],
                "processing_time": quick_result.get("processing_time_seconds", 0)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# 🔍 RESULT
@router.get("/result/{request_id}")
def get_result(
    request_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        detection = db.query(Detection).filter(
            Detection.request_id == request_id,
            Detection.user_id == current_user.id
        ).first()

        if not detection:
            raise HTTPException(status_code=404, detail="Not found")

        return {
            "request_id": detection.request_id,
            "status": detection.status,
            "results": detection.results or {}
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch result: {str(e)}")


# 📊 HISTORY (WITH PAGINATION 🚀)
@router.get("/history")
def get_history(
    limit: int = Query(10, le=50),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        detections = db.query(Detection).filter(
            Detection.user_id == current_user.id
        ).order_by(Detection.created_at.desc()).offset(offset).limit(limit).all()

        history_data = []

        for d in detections:
            results = d.results or {}

            history_data.append({
                "request_id": d.request_id,
                "filename": d.filename,
                "status": d.status,
                "summary": {
                    "total_objects": results.get("total_objects"),
                    "objects": [obj.get("label") for obj in results.get("objects", [])],
                    "processing_time": results.get("processing_time_seconds")
                },
                "created_at": d.created_at
            })

        return {
            "count": len(history_data),
            "data": history_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")