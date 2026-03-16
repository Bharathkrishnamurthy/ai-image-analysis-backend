from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as image_router
from app.api.auth_routes import router as auth_router

from app.db.database import engine
from app.db.models import Base

print("🔥 MAIN FILE LOADED 🔥")

app = FastAPI(
    title="AI Image Analysis API",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(image_router, prefix="/image", tags=["Image"])


@app.on_event("startup")
def on_startup():
    print("🚀 Starting application...")

    # Ensure DB tables exist
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables ensured.")

    print("🤖 YOLO model ready for inference.")


@app.get("/")
def root():
    return {
        "message": "AI Image Analysis Backend is Running 🚀",
        "status": "active"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}