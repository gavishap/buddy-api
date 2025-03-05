from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class MessageBase(BaseModel):
    """Base message schema."""
    content: str
    is_read: bool = False

class MessageCreate(MessageBase):
    """Message creation schema."""
    sender_id: str
    receiver_id: str
    booking_id: Optional[str] = None

class MessageUpdate(BaseModel):
    """Message update schema."""
    is_read: Optional[bool] = None

class MessageInDBBase(MessageBase):
    """Base schema for messages in DB."""
    id: str = Field(..., alias="id")
    sender_id: str
    receiver_id: str
    booking_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Message(MessageInDBBase):
    """Message schema for API responses."""
    pass

class MessageWithDetails(Message):
    """Message schema with sender and receiver details."""
    sender: Dict[str, Any]
    receiver: Dict[str, Any]
    booking: Optional[Dict[str, Any]] = None

class ConversationSummary(BaseModel):
    """Conversation summary schema."""
    other_user: Dict[str, Any]
    last_message: Dict[str, Any]
    unread_count: int
    last_updated: datetime 
