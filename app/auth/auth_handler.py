import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.models import User

# 🔐 SECRET KEY
SECRET_KEY = os.getenv("SECRET_KEY", "local_dev_secret_key")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 🔐 VERIFY PASSWORD (supports old + new users)
def verify_password(plain_password: str, stored_password: str):
    # 🔥 bcrypt users
    if stored_password.startswith("$2b$"):
        return pwd_context.verify(plain_password, stored_password)

    # 🔥 old plain text users
    return plain_password == stored_password


# ✅ AUTHENTICATE USER (USES DB SESSION FROM DEPENDENCY)
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    return user


# ✅ CREATE TOKEN
def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "sub": data.get("sub")  # 🔥 must match get_current_user
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)