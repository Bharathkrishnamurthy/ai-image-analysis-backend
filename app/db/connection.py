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

# ✅ Create engine (production-ready config)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,     # 🔥 auto reconnect if DB drops
    pool_size=5,            # number of persistent connections
    max_overflow=10,        # extra connections if needed
    pool_timeout=30,        # wait time before error
    pool_recycle=1800,      # recycle connections (fixes stale issues)
    echo=False              # set True for SQL debugging
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
        db.rollback()   # 🔥 prevents broken transactions
        raise
    finally:
        db.close()