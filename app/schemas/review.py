from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

class ReviewBase(BaseModel):
    """Base review schema."""
    rating: int
    comment: Optional[str] = None
    
    @validator('rating')
    def rating_must_be_between_1_and_5(cls, v):
        if v < 1 or v > 5:
            raise ValueError('rating must be between 1 and 5')
        return v

class ReviewCreate(ReviewBase):
    """Review creation schema."""
    booking_id: str
    owner_id: str
    sitter_id: str

class ReviewUpdate(BaseModel):
    """Review update schema."""
    rating: Optional[int] = None
    comment: Optional[str] = None
    
    @validator('rating')
    def rating_must_be_between_1_and_5(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('rating must be between 1 and 5')
        return v

class ReviewInDBBase(ReviewBase):
    """Base schema for reviews in DB."""
    id: str = Field(..., alias="id")
    booking_id: str
    owner_id: str
    sitter_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Review(ReviewInDBBase):
    """Review schema for API responses."""
    pass

class ReviewWithDetails(Review):
    """Review schema with owner and sitter details."""
    owner: Dict[str, Any]
    sitter: Dict[str, Any]
    booking: Dict[str, Any] 
