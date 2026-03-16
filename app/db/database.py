from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Use environment variable if available, otherwise default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:5052586@host.docker.internal:5432/ai_db"
)

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

print("✅ Database connected:", DATABASE_URL)