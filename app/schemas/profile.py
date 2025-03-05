from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

class ProfileBase(BaseModel):
    """Base profile schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    user_type: str  # "owner" or "sitter"
    avatar_url: Optional[str] = None

class ProfileCreate(ProfileBase):
    """Profile creation schema."""
    user_id: str

class ProfileUpdate(BaseModel):
    """Profile update schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None

class ProfileInDBBase(ProfileBase):
    """Base schema for profiles in DB."""
    id: str = Field(..., alias="id")
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Profile(ProfileInDBBase):
    """Profile schema for API responses."""
    pass

class SitterProfileBase(ProfileBase):
    """Base schema for sitter profiles."""
    bio: Optional[str] = None
    services: Optional[List[str]] = None  # ["dog_walking", "pet_sitting", "boarding"]
    hourly_rate: Optional[float] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = 0

class SitterProfileCreate(SitterProfileBase, ProfileCreate):
    """Sitter profile creation schema."""
    pass

class SitterProfileUpdate(ProfileUpdate):
    """Sitter profile update schema."""
    bio: Optional[str] = None
    services: Optional[List[str]] = None
    hourly_rate: Optional[float] = None

class SitterProfile(SitterProfileBase, Profile):
    """Sitter profile schema for API responses."""
    pass 
