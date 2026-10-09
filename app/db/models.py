
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    password = Column(
        String,
        nullable=False,
    )

    detections = relationship(
        "Detection",
        back_populates="user",
    )


class Detection(Base):
    __tablename__ = "detections"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    request_id = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    filename = Column(
        String,
        nullable=False,
    )

    image_path = Column(
        String,
        nullable=True,
    )

    status = Column(
        String,
        default="pending",
        nullable=False,
        index=True,
    )

    prediction = Column(
        String,
        nullable=True,
    )

    confidence = Column(
        String,
        nullable=True,
    )

    results = Column(
        JSON,
        nullable=True,
    )

    processing_time = Column(
        String,
        nullable=True,
    )

    model_version = Column(
        String,
        default="yolo-v1",
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    user = relationship(
        "User",
        back_populates="detections",
    )
