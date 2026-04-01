from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.api.routes import router as image_router
from app.api.auth_routes import router as auth_router
from app.api.task_routes import router as task_router

from app.db.connection import engine
from app.db.models import Base


# ✅ Lifespan (startup + migration)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up...")

    # ✅ Create tables
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created")
    except Exception as e:
        print("❌ Table creation error:", e)

    # ✅ SAFE MIGRATIONS (🔥 ALL REQUIRED COLUMNS)
    try:
        with engine.begin() as conn:

            # request_id
            conn.execute(text("""
                ALTER TABLE detections
                ADD COLUMN IF NOT EXISTS request_id VARCHAR;
            """))

            # 🔥 FIX YOUR ERROR
            conn.execute(text("""
                ALTER TABLE detections
                ADD COLUMN IF NOT EXISTS image_path VARCHAR;
            """))

            # filename (safety)
            conn.execute(text("""
                ALTER TABLE detections
                ADD COLUMN IF NOT EXISTS filename VARCHAR;
            """))

            # status
            conn.execute(text("""
                ALTER TABLE detections
                ADD COLUMN IF NOT EXISTS status VARCHAR;
            """))

            # results (JSON)
            conn.execute(text("""
                ALTER TABLE detections
                ADD COLUMN IF NOT EXISTS results JSON;
            """))

            # created_at
            conn.execute(text("""
                ALTER TABLE detections
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;
            """))

            # user_id
            conn.execute(text("""
                ALTER TABLE detections
                ADD COLUMN IF NOT EXISTS user_id INTEGER;
            """))

        print("✅ All migrations applied")

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


# ✅ App
app = FastAPI(
    title="AI Image Analysis API",
    version="1.0.0",
    lifespan=lifespan
)


# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ restrict in production later
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


# ✅ Health check
@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "db error", "error": str(e)}