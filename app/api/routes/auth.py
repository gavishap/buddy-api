"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime
from passlib.context import CryptContext

from app.core.config import settings, collections
from app.db.mongodb import get_database

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint."""
    # For now, just return a mock success response
    return {
        "access_token": "mock_token",
        "token_type": "bearer",
        "user_id": "mock_user_id",
        "user_type": "owner",  # or "sitter"
    }


@router.post("/register/owner")
async def register_owner(user_data: UserRegister):
    """Register a new pet owner."""
    db = get_database()
    
    # Check if user already exists
    existing_user = await db[collections.USERS].find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create user document
    user_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    
    # Hash the password
    hashed_password = pwd_context.hash(user_data.password)
    
    # User document
    user = {
        "id": user_id,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "user_type": "owner",
        "created_at": created_at,
        "is_active": True
    }
    
    # Profile document
    profile = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "created_at": created_at,
        "updated_at": created_at
    }
    
    # Insert user and profile
    await db[collections.USERS].insert_one(user)
    await db[collections.PROFILES].insert_one(profile)
    
    return {
        "message": "Owner registered successfully",
        "user_id": user_id
    }


@router.post("/register/sitter")
async def register_sitter(user_data: UserRegister):
    """Register a new pet sitter."""
    db = get_database()
    
    # Check if user already exists
    existing_user = await db[collections.USERS].find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create user document
    user_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    
    # Hash the password
    hashed_password = pwd_context.hash(user_data.password)
    
    # User document
    user = {
        "id": user_id,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "user_type": "sitter",
        "created_at": created_at,
        "is_active": True
    }
    
    # Profile document
    profile = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "created_at": created_at,
        "updated_at": created_at
    }
    
    # Insert user and profile
    await db[collections.USERS].insert_one(user)
    await db[collections.PROFILES].insert_one(profile)
    
    return {
        "message": "Sitter registered successfully",
        "user_id": user_id
    }


@router.post("/logout")
async def logout():
    """Logout endpoint."""
    return {"message": "Logged out successfully"} 
