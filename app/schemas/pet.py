from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field

class PetBase(BaseModel):
    """Base pet schema."""
    name: str
    species: str  # "dog", "cat", "bird", etc.
    breed: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None  # in kg
    gender: Optional[str] = None  # "male", "female"
    description: Optional[str] = None
    special_requirements: Optional[str] = None
    is_active: bool = True
    photo_url: Optional[str] = None

class PetCreate(PetBase):
    """Pet creation schema."""
    owner_id: str

class PetUpdate(BaseModel):
    """Pet update schema."""
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    special_requirements: Optional[str] = None
    is_active: Optional[bool] = None
    photo_url: Optional[str] = None

class PetInDBBase(PetBase):
    """Base schema for pets in DB."""
    id: str = Field(..., alias="id")
    owner_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Pet(PetInDBBase):
    """Pet schema for API responses."""
    pass

class PetWithOwner(Pet):
    """Pet schema with owner information."""
    owner: dict  # Simplified owner information 
