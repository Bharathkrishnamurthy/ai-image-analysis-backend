from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.db.connection import get_db
from app.db.models import Detection
from app.services.yolo_service import detect_objects

import shutil
import os
import uuid
import json

router = APIRouter()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# 🔥 IMAGE UPLOAD + AI ANALYSIS
@router.post("/predict")
def predict_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:

        # Generate unique filename
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save uploaded image
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 🔥 Run YOLO object detection
        detection_result = detect_objects(file_path)

        # Convert result to JSON-safe format
        detection_json = json.loads(json.dumps(detection_result))

        # Save result to database
        detection = Detection(
            filename=filename,
            results=detection_json,
            user_id=current_user.id
        )

        db.add(detection)
        db.commit()
        db.refresh(detection)

        return {
            "message": "Image analyzed successfully",
            "filename": filename,
            "user_id": current_user.id,
            "detections": detection_json
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔥 USER-SPECIFIC HISTORY
@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    detections = db.query(Detection).filter(
        Detection.user_id == current_user.id
    ).all()

    return detections