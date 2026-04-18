from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.api.routes import router as image_router
from app.api.auth_routes import router as auth_router
from app.api.task_routes import router as task_router

from app.db.connection import engine
from app.db.models import Base

import os
from dotenv import load_dotenv

# 🔹 Load env variables
load_dotenv()

print("CLOUD:", os.getenv("CLOUD_NAME"))
print("API_KEY:", os.getenv("API_KEY"))
print("API_SECRET:", os.getenv("API_SECRET"))
print("REDIS_URL:", os.getenv("REDIS_URL"))


# 🚀 Lifespan (startup logic)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up...")

    # ✅ STEP 1: Ensure DB connection works
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connected")
    except OperationalError as e:
        print("❌ DATABASE CONNECTION FAILED:", e)
        raise e  # 🚨 Stop app if DB fails

    # ✅ STEP 2: Create tables (CRITICAL)
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
    except Exception as e:
        print("❌ Table creation failed:", e)
        raise e  # 🚨 Stop app if tables fail

    # ✅ STEP 3: Safe migrations (only if table exists)
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'detections'
                );
            """)).scalar()

            if result:
                migrations = [
                    "ADD COLUMN IF NOT EXISTS request_id VARCHAR",
                    "ADD COLUMN IF NOT EXISTS image_path VARCHAR",
                    "ADD COLUMN IF NOT EXISTS filename VARCHAR",
                    "ADD COLUMN IF NOT EXISTS status VARCHAR",
                    "ADD COLUMN IF NOT EXISTS results JSON",
                    "ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",
                    "ADD COLUMN IF NOT EXISTS user_id INTEGER"
                ]

                for migration in migrations:
                    conn.execute(text(f"ALTER TABLE detections {migration};"))

                print("✅ Migrations applied")
            else:
                print("⚠️ 'detections' table not found, skipping migrations")

    except Exception as e:
        print("⚠️ Migration error:", e)

    yield

    print("🛑 Shutting down...")


# 🚀 Create FastAPI app
app = FastAPI(
    title="AI Image Analysis API",
    version="1.0.0",
    lifespan=lifespan
)


# 🌐 Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🔗 Include routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(image_router, prefix="/image", tags=["Image"])
app.include_router(task_router, prefix="/task", tags=["Task"])


# 🏠 Root endpoint
@app.get("/")
def root():
    return {"message": "API running 🚀"}


# ❤️ Health check
@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "db error", "error": str(e)}