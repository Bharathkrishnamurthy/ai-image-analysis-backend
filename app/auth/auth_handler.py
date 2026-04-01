import os
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

from app.db.connection import SessionLocal
from app.db.models import User

# 🔐 SAFE SECRET KEY (works locally + production)
SECRET_KEY = os.getenv("SECRET_KEY", "local_dev_secret_key")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ✅ AUTHENTICATE USER
def authenticate_user(username: str, password: str):
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return False

        if not pwd_context.verify(password, user.password):
            return False

        return {
            "username": user.username,
            "id": user.id
        }

    finally:
        db.close()


# ✅ CREATE TOKEN
def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "sub": data.get("username")
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)