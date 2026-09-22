import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import User

router = APIRouter()

SECRET_KEY = "super-secret-key-for-accessgov-demo"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    email: str
    password: str
    name: str = ""
    age: Optional[int] = None

class UserLogin(BaseModel):
    email: str
    password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, password_hash=hashed_password, name=user.name, age=user.age)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token(data={"sub": new_user.email, "user_id": new_user.id})
    return {"access_token": token, "token_type": "bearer", "user_id": new_user.id, "name": new_user.name}

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    token = create_access_token(data={"sub": db_user.email, "user_id": db_user.id})
    return {"access_token": token, "token_type": "bearer", "user_id": db_user.id, "name": db_user.name}

@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": db_user.id,
        "email": db_user.email,
        "name": db_user.name,
        "age": db_user.age,
        "accessibility_prefs": db_user.accessibility_prefs
    }

class PrefsUpdate(BaseModel):
    prefs: dict

@router.put("/users/{user_id}/prefs")
def update_prefs(user_id: int, prefs_update: PrefsUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Merge existing prefs with new prefs
    current_prefs = db_user.accessibility_prefs or {}
    current_prefs.update(prefs_update.prefs)
    
    db_user.accessibility_prefs = current_prefs
    db.commit()
    return {"status": "success", "accessibility_prefs": current_prefs}
