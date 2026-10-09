
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DetectionBase(BaseModel):
    filename: str
    object_count: int
    confidence_threshold: float
    processing_time: float


class DetectionResponse(DetectionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
