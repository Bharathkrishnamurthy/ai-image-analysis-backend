from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

# 🔥 Load .env
load_dotenv()

# 🔥 Get DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

# ✅ Fallback to SQLite if not set (VERY IMPORTANT)
if not DATABASE_URL:
    print("⚠️ DATABASE_URL not found, using SQLite fallback")
    DATABASE_URL = "sqlite:///./test.db"

# 🔥 Fix for Render / old postgres URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 🔥 Special handling for SQLite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# 🔥 Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
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