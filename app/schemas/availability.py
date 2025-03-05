from typing import Optional, List
from datetime import datetime, date, time
from pydantic import BaseModel, Field, validator
from enum import Enum

class DayOfWeek(str, Enum):
    """Day of week enum."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

class RecurringAvailabilityBase(BaseModel):
    """Base recurring availability schema."""
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    
    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class RecurringAvailabilityCreate(RecurringAvailabilityBase):
    """Recurring availability creation schema."""
    sitter_id: str

class RecurringAvailabilityUpdate(BaseModel):
    """Recurring availability update schema."""
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class RecurringAvailabilityInDBBase(RecurringAvailabilityBase):
    """Base schema for recurring availabilities in DB."""
    id: str = Field(..., alias="id")
    sitter_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class RecurringAvailability(RecurringAvailabilityInDBBase):
    """Recurring availability schema for API responses."""
    pass

class SpecificAvailabilityBase(BaseModel):
    """Base specific availability schema."""
    date: date
    start_time: time
    end_time: time
    
    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class SpecificAvailabilityCreate(SpecificAvailabilityBase):
    """Specific availability creation schema."""
    sitter_id: str
    is_available: bool = True  # True for available, False for unavailable (override)

class SpecificAvailabilityUpdate(BaseModel):
    """Specific availability update schema."""
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_available: Optional[bool] = None

class SpecificAvailabilityInDBBase(SpecificAvailabilityBase):
    """Base schema for specific availabilities in DB."""
    id: str = Field(..., alias="id")
    sitter_id: str
    is_available: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class SpecificAvailability(SpecificAvailabilityInDBBase):
    """Specific availability schema for API responses."""
    pass

class AvailabilityResponse(BaseModel):
    """Combined availability response schema."""
    recurring: List[RecurringAvailability]
    specific: List[SpecificAvailability] 
