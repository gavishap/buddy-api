from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from pydantic import BaseModel, Field, validator
from enum import Enum

class BookingStatus(str, Enum):
    """Booking status enum."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class ServiceType(str, Enum):
    """Service type enum."""
    DOG_WALKING = "dog_walking"
    PET_SITTING = "pet_sitting"
    BOARDING = "boarding"
    GROOMING = "grooming"
    TRAINING = "training"

class BookingBase(BaseModel):
    """Base booking schema."""
    service_type: ServiceType
    start_date: date
    end_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    notes: Optional[str] = None
    status: BookingStatus = BookingStatus.PENDING
    total_price: Optional[float] = None

    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

class BookingCreate(BookingBase):
    """Booking creation schema."""
    owner_id: str
    sitter_id: str
    pet_ids: List[str]

class BookingUpdate(BaseModel):
    """Booking update schema."""
    service_type: Optional[ServiceType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    notes: Optional[str] = None
    status: Optional[BookingStatus] = None
    total_price: Optional[float] = None
    pet_ids: Optional[List[str]] = None

class BookingInDBBase(BookingBase):
    """Base schema for bookings in DB."""
    id: str = Field(..., alias="id")
    owner_id: str
    sitter_id: str
    pet_ids: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Booking(BookingInDBBase):
    """Booking schema for API responses."""
    pass

class BookingWithDetails(Booking):
    """Booking schema with owner, sitter, and pet details."""
    owner: Dict[str, Any]
    sitter: Dict[str, Any]
    pets: List[Dict[str, Any]] 
