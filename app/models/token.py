"""Token models."""
from pydantic import BaseModel


class Token(BaseModel):
    """Token model."""
    access_token: str
    token_type: str 
