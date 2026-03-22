from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.db.connection import get_db
from app.services.inference_service import run_inference_pipeline

import shutil
import os
import uuid

router = APIRouter()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/predict")
def predict_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        # ✅ Unique filename
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # ✅ Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 🔥 RUN IN BACKGROUND (key change)
        background_tasks.add_task(
            run_inference_pipeline,
            file_path,
            current_user.id,
            filename
        )

        return {
            "message": "Processing started 🚀",
            "filename": filename,
            "status": "queued"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))