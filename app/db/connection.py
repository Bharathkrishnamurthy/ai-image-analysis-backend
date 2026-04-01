import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 🔥 Load DATABASE_URL from environment (Render / local)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:admin123@127.0.0.1:5432/ai_db"
)

# 🔥 Fix Render DB URL (important)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg://",
        1
    )
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )

# 🔌 Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True  # 🔥 avoids stale connections
)

# 🧠 Session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ✅ Dependency (FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()