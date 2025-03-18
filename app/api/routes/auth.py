"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
from typing import Optional

from app.core.config import settings, collections
from app.db.mongodb import get_database
from app.models.token import Token
from app.models.user import UserCreate, UserLogin, User
from app.core.security import create_access_token, get_password_hash, verify_password

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Define request models
class UserRegister(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

async def authenticate_user(email: str, password: str):
    """Authenticate user with email and password."""
    db = get_database()
    user = await db[collections.USERS].find_one({"email": email})
    
    if not user:
        return False
    
    # If no hashed_password, try password field
    stored_password = user.get("hashed_password", user.get("password"))
    if not stored_password:
        return False
    
    if not verify_password(password, stored_password):
        return False
    
    # Add id if not exists
    if "id" not in user and "_id" in user:
        user["id"] = str(user["_id"])
    
    return user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user with email and password."""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    user_id = str(user.get("id", user.get("_id", "")))
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Alternative endpoint for mobile app
@router.post("/token", response_model=Token)
async def login_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user with email and password - alternative endpoint."""
    return await login(form_data)

@router.get("/me")
async def get_current_user():
    """Get current user info."""
    # For now, just return a mock user
    return {
        "id": "mock_user_id",
        "email": "user@example.com",
        "user_type": "owner",
    }

# Duplicate route to match the pattern the mobile app is using
@router.get("/auth/me")
async def get_current_user_auth_auth():
    """Duplicate get current user endpoint for compatibility."""
    return await get_current_user()

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user."""
    db = get_database()
    
    # Check if user already exists
    existing_user = await db[collections.USERS].find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user dict
    user_dict = user_data.dict()
    user_dict["hashed_password"] = hashed_password
    del user_dict["password"]  # Remove plain password
    
    # Insert user
    result = await db[collections.USERS].insert_one(user_dict)
    user_id = str(result.inserted_id)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Separate endpoints for owner and sitter registration (for API structure)
@router.post("/register/owner", response_model=Token)
async def register_owner(user_data: UserCreate):
    """Register a new owner."""
    user_data.user_type = "owner"
    return await register(user_data)

@router.post("/register/sitter", response_model=Token)
async def register_sitter(user_data: UserCreate):
    """Register a new sitter."""
    user_data.user_type = "sitter"
    return await register(user_data)

@router.post("/logout")
async def logout():
    """Logout endpoint."""
    return {"message": "Logged out successfully"} 
