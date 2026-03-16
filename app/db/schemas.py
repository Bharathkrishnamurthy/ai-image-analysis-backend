from pydantic import BaseModel
from datetime import datetime


class DetectionBase(BaseModel):
    filename: str
    object_count: int
    confidence_threshold: float
    processing_time: float


class DetectionResponse(DetectionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True