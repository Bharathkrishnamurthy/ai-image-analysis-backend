import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ✅ Get DB URL (with safe default)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:admin123@127.0.0.1:5432/ai_db"
)

# ✅ Fix URL compatibility (important for deployment platforms)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://", "postgresql+psycopg://", 1
    )
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

# ✅ Detect Supabase (pooler) → enforce SSL
connect_args = {}
if "supabase.com" in DATABASE_URL:
    connect_args = {"sslmode": "require"}   # 🔥 REQUIRED for Supabase

# ✅ Create engine (OPTIMIZED for Supabase)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,

    # 🔥 IMPORTANT FIX (reduce connections → avoid circuit breaker)
    pool_size=3,          # was 5 → reduced
    max_overflow=2,       # was 10 → reduced

    pool_timeout=30,
    pool_recycle=300,     # was 1800 → faster recycle (important)

    connect_args=connect_args,
    echo=False
)

# ✅ Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# ✅ Base model
Base = declarative_base()


# ✅ Dependency (used in FastAPI routes)
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()