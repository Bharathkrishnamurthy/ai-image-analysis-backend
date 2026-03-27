from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

# 🔥 Load .env file (IMPORTANT)
load_dotenv()

# 🔥 Get DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL environment variable is not set")

# 🔥 Fix for Render + Postgres (important)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 🔥 Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True  # ✅ avoids stale connections
)

# 🔥 Session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 🔥 Base model
Base = declarative_base()

print("✅ Database configuration loaded")