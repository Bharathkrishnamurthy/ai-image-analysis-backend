from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 🔥 Database URL (make sure password is correct)
DATABASE_URL = "postgresql://postgres:admin123@127.0.0.1:5432/ai_db"

# 🔌 Engine (✅ FIXED — removed SQLite-only config)
engine = create_engine(
    DATABASE_URL
)

# 🧠 Session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ✅ Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()