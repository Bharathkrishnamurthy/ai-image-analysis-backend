from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from app.db.database import Base
from datetime import datetime

class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String, nullable=False)

    results = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    # NEW FIELD (Phase 6)
    user_id = Column(Integer, ForeignKey("users.id"))