"""User models."""
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    user_type: str = "owner"  # Default to owner


class UserCreate(UserBase):
    """User creation model."""
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class User(UserBase):
    """User model."""
    id: str
    is_active: bool = True

    class Config:
        orm_mode = True 
