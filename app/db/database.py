from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

# 🔥 Load .env
load_dotenv()

# 🔥 Get DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

# ✅ Fallback to SQLite if not set
if not DATABASE_URL:
    print("⚠️ DATABASE_URL not found, using SQLite fallback")
    DATABASE_URL = "sqlite:///./test.db"

# 🔥 Fix postgres URL (IMPORTANT)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# 🔥 Special handling
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# 🔥 Supabase requires SSL
if "supabase.com" in DATABASE_URL:
    connect_args["sslmode"] = "require"

# 🔥 Create engine (FIXED – prevent overload)
engine = create_engine(
    DATABASE_URL,
    echo=False,              # ❌ was True (too noisy + slow)
    pool_pre_ping=True,

    # 🔥 IMPORTANT FIX (same as connection.py)
    pool_size=3,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=300,

    connect_args=connect_args
)

# 🔥 Session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 🔥 Base
Base = declarative_base()

print(f"✅ Database connected using: {DATABASE_URL}")