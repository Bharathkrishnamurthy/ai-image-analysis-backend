from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.api.routes import router as image_router
from app.api.auth_routes import router as auth_router
from app.api.task_routes import router as task_router

from app.db.connection import engine
from app.db.models import Base


# 🚀 Lifespan (startup + migration)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up...")

    # ✅ Create tables
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created")
    except Exception as e:
        print("❌ Table creation error:", e)

    # ✅ Safe migrations
    try:
        with engine.begin() as conn:
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
                try:
                    conn.execute(text(f"ALTER TABLE detections {migration};"))
                except Exception as e:
                    print(f"⚠️ Skipping migration: {migration} | Error: {e}")

        print("✅ Migrations applied")

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


# 🚀 FastAPI app
app = FastAPI(
    title="AI Image Analysis API",
    version="1.0.0",
    lifespan=lifespan
)


# 🌐 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🔗 Routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(image_router, prefix="/image", tags=["Image"])
app.include_router(task_router, prefix="/task", tags=["Task"])


# 🏠 Root
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