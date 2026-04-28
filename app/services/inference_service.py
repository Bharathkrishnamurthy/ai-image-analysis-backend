from app.services.yolo_service import detect_objects
from app.db.connection import SessionLocal
from app.db.models import Detection

import logging
import time

logger = logging.getLogger(__name__)


def run_inference_pipeline(image_path: str, request_id: str):
    db = SessionLocal()

    try:
        logger.info(f"🚀 Starting inference for {request_id}")

        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if not detection:
            logger.error(f"❌ No detection found for {request_id}")
            return

        start_time = time.time()

        # 🔥 Run YOLO
        raw_result = detect_objects(image_path)

        end_time = time.time()

        # ==============================
        # 🔥 STEP 1: Clean + Filter objects
        # ==============================
        objects_list = []
        clean_objects = []

        for obj in raw_result:
            confidence = round(obj.get("confidence", 0) * 100, 2)

            # 👉 filter weak detections
            if confidence < 40:
                continue

            label = obj.get("label", "unknown")

            objects_list.append({
                "object": label,
                "confidence": f"{confidence}%"
            })

            clean_objects.append({
                "label": label,
                "confidence": confidence
            })

        total_objects = len(objects_list)

        # ==============================
        # 🔥 STEP 2: Scene Intelligence (weighted logic)
        # ==============================
        scene_scores = {
            "Living Room": 0,
            "Outdoor": 0,
            "Office": 0,
            "Crowded Area": 0
        }

        for obj in clean_objects:
            label = obj["label"]
            conf = obj["confidence"] / 100

            if label in ["person", "tv", "sofa"]:
                scene_scores["Living Room"] += conf

            if label in ["car", "truck", "bus"]:
                scene_scores["Outdoor"] += conf

            if label in ["laptop", "keyboard"]:
                scene_scores["Office"] += conf

            if label == "person":
                scene_scores["Crowded Area"] += conf

        # pick best scene
        scene_label = max(scene_scores, key=scene_scores.get)
        scene_confidence = round(scene_scores[scene_label], 2)

        # ==============================
        # 🔥 STEP 3: Risk Scoring (numeric)
        # ==============================
        risk_score = 0

        person_count = sum(1 for o in clean_objects if o["label"] == "person")

        if person_count >= 5:
            risk_score += 0.5

        if person_count >= 10:
            risk_score += 0.8

        for obj in clean_objects:
            if obj["label"] in ["knife", "fire"]:
                risk_score += 1.0

        risk_score = min(risk_score, 1.0)

        if risk_score > 0.7:
            risk_level = "High"
        elif risk_score > 0.3:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # ==============================
        # 🔥 STEP 4: Insight Generation (smart text)
        # ==============================
        if scene_label == "Living Room":
            insight = f"Indoor environment detected with {person_count} people, likely a social or family setting."
        elif scene_label == "Outdoor":
            insight = f"Outdoor scene with moving objects, possibly traffic or public area."
        elif scene_label == "Office":
            insight = "Workspace environment detected with electronic devices."
        elif scene_label == "Crowded Area":
            insight = f"Crowded environment with {person_count} people detected."
        else:
            insight = f"{total_objects} objects detected."

        # ==============================
        # 🔥 FINAL RESPONSE
        # ==============================
        detection.status = "completed"
        detection.results = {
            "summary": f"Detected {total_objects} object(s)",
            "scene": {
                "label": scene_label,
                "confidence": scene_confidence
            },
            "risk": {
                "level": risk_level,
                "score": round(risk_score, 2)
            },
            "insight": insight,
            "total_objects": total_objects,
            "objects": objects_list,
            "processing_time": f"{round(end_time - start_time, 2)} seconds"
        }

        db.commit()
        db.refresh(detection)

        logger.info(f"✅ Inference completed for {request_id}")

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {str(e)}")

        detection = db.query(Detection).filter(
            Detection.request_id == request_id
        ).first()

        if detection:
            detection.status = "failed"
            detection.results = {
                "summary": "Processing failed",
                "error": str(e)
            }
            db.commit()

    finally:
        db.close()