
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import router as image_router
from app.api.auth_routes import router as auth_router
from app.api.task_routes import router as task_router

from app.db.connection import engine
from app.db.models import Base, User, Detection


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Image Analysis API")

    try:
        # Check database connectivity.
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.info("Database connection successful")

        # Create missing tables.
        # Existing tables are not automatically migrated.
        Base.metadata.create_all(bind=engine)

        logger.info("Database table initialization completed")

    except SQLAlchemyError:
        logger.exception("Database initialization failed")
        engine.dispose()
        raise

    try:
        yield
    finally:
        engine.dispose()
        logger.info("AI Image Analysis API shut down")


app = FastAPI(
    title="AI Image Analysis API",
    description="API for image analysis, authentication, and background tasks",
    version="1.0.0",
    lifespan=lifespan,
)


# Update these origins to match your frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Auth"],
)

app.include_router(
    image_router,
    prefix="/image",
    tags=["Image"],
)

app.include_router(
    task_router,
    prefix="/task",
    tags=["Task"],
)


@app.get("/")
def root():
    return {
        "message": "AI Image Analysis API is running"
    }


@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except SQLAlchemyError:
        logger.exception("Health check database connection failed")

        return {
            "status": "unhealthy",
            "database": "disconnected",
        }
