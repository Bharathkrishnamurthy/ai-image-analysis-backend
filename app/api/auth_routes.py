from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.auth_handler import authenticate_user, create_access_token, pwd_context
from app.db.connection import get_db
from app.db.models import User

router = APIRouter()


# 🧾 Request schema
class RegisterRequest(BaseModel):
    username: str
    password: str


# ✅ REGISTER
@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # 🔍 Check if user already exists
    existing_user = db.query(User).filter(User.username == request.username).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    # 🔐 Hash password using SAME context
    hashed_password = pwd_context.hash(request.password)

    new_user = User(
        username=request.username,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully"
    }


# ✅ LOGIN
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # 🔐 Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 🔥 Create JWT (IMPORTANT: use "sub")
    access_token = create_access_token({
        "sub": user.username
    })

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }