from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    """User creation schema."""
    password: str
    first_name: str
    last_name: str
    user_type: str = "owner"  # "owner" or "sitter"

class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class UserInDBBase(UserBase):
    """Base schema for users in DB."""
    id: str = Field(..., alias="id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class User(UserInDBBase):
    """User schema for API responses."""
    pass

class UserInDB(UserInDBBase):
    """User schema for DB operations."""
    hashed_password: str 
