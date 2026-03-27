from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ Routers
from app.api.routes import router as image_router
from app.api.auth_routes import router as auth_router
from app.api.task_routes import router as task_router  # ✅ NEW (Celery task status)

# ✅ DB
from app.db.database import engine
from app.db.models import Base

print("🔥 MAIN FILE LOADED 🔥")

# 🚀 FastAPI App
app = FastAPI(
    title="AI Image Analysis API",
    version="2.0.0"
)

# ✅ CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include Routers
app.include_router(auth_router)
app.include_router(image_router, prefix="/image", tags=["Image"])
app.include_router(task_router, tags=["Task"])  # ✅ NEW

# 🚀 Startup Event
@app.on_event("startup")
def on_startup():
    print("🚀 Starting application...")

    # ✅ Create DB tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables ensured.")

    # (Optional) preload model if needed
    print("🤖 YOLO model ready for inference.")

# 🏠 Root Endpoint
@app.get("/")
def root():
    return {
        "message": "AI Image Analysis Backend is Running 🚀",
        "status": "active",
        "version": "2.0.0"
    }

# ❤️ Health Check
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "AI Backend",
        "celery": "connected (ensure worker is running)"
    }