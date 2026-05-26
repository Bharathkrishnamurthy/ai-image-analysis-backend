from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.database import Base

class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    image_url = Column(String, nullable=False)

    prediction = Column(String, nullable=False)

    confidence = Column(Float, nullable=False)

    status = Column(String, default="COMPLETED")

    created_at = Column(DateTime(timezone=True), server_default=func.now())