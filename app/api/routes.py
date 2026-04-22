from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
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
from datetime import datetime
import tempfile
import shutil

router = APIRouter()

# ✅ Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

# 🔥 OPTIONAL toggle (disable Celery if not needed)
USE_BACKGROUND_TASK = False


# 🚀 PREDICT (FINAL)
@router.post("/predict")
def predict_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    temp_path = None

    try:
        # ✅ File type validation
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Invalid file type")

        # ✅ OPTIONAL file size limit (5MB)
        file.file.seek(0, 2)  # move to end
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 5MB)")

        filename = f"{uuid.uuid4()}_{file.filename}"
        request_id = str(uuid.uuid4())

        # ✅ Save temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        shutil.copyfileobj(file.file, temp_file)
        temp_file.close()
        temp_path = temp_file.name

        # 🔥 Reset pointer
        file.file.seek(0)

        # ✅ Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(temp_path)
        image_url = upload_result.get("secure_url")

        if not image_url:
            raise HTTPException(status_code=500, detail="Cloud upload failed")

        # 🔥 FULL DETECTION (SYNC)
        full_result = detect_objects(temp_path, confidence_threshold=0.25)

        if "error" in full_result:
            raise Exception(full_result["error"])

        # ✅ Format objects
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

        analytics = dict(sorted(analytics.items(), key=lambda x: x[1], reverse=True))

        # ✅ Final result
        final_result = {
            "summary": f"Detected {full_result.get('total_objects', 0)} object(s)",
            "total_objects": full_result.get("total_objects", 0),
            "objects": objects_list,
            "analytics": analytics,
            "processing_time": full_result.get("processing_time"),
            "status": "success"
        }

        # ✅ Save to DB
        detection = Detection(
            filename=filename,
            request_id=request_id,
            image_path=image_url,
            status="completed",
            results=final_result,
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )

        db.add(detection)
        db.commit()
        db.refresh(detection)

        # 🔥 OPTIONAL background task
        if USE_BACKGROUND_TASK:
            run_inference_task.delay(image_url, request_id)

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
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


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
                "image_url": d.image_path,
                "created_at": d.created_at
            }
            for d in detections
        ]
    }