from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.api.routes import router as image_router
from app.api.auth_routes import router as auth_router
from app.api.task_routes import router as task_router

from app.db.connection import engine
from app.db.models import Base


# ✅ Lifespan (replaces deprecated startup event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up...")

    # ✅ Ensure DB tables exist
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created")
    except Exception as e:
        print("❌ Table creation error:", e)

    # ✅ Safe migration (column auto-add)
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE detections
                ADD COLUMN IF NOT EXISTS request_id VARCHAR;
            """))
        print("✅ Migration checked")
    except Exception as e:
        print("⚠️ Migration error:", e)

    # ✅ DB connection check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connected")
    except Exception as e:
        print("❌ Database connection failed:", e)

    yield

    print("🛑 Shutting down...")


# ✅ Create app
app = FastAPI(
    title="AI Image Analysis API",
    version="1.0.0",
    lifespan=lifespan
)


# ✅ CORS (fix later for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ Routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(image_router, prefix="/image", tags=["Image"])
app.include_router(task_router, prefix="/task", tags=["Task"])


# ✅ Root
@app.get("/")
def root():
    return {"message": "API running"}


# ✅ Health check (important for debugging)
@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "db error", "error": str(e)}