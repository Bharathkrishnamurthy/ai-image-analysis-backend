from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.connection import Base


# ✅ USER MODEL (FIXED)
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}  # 🔥 FIX FOR YOUR ERROR

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    detections = relationship("Detection", back_populates="user")


# ✅ DETECTION MODEL
class Detection(Base):
    __tablename__ = "detections"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True, nullable=False)

    filename = Column(String, nullable=False)
    image_path = Column(String, nullable=True)

    status = Column(String, default="processing", nullable=False)

    results = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="detections")