"""App configuration."""
import os
from typing import Dict, List

from pydantic_settings import BaseSettings


class Collections:
    """Database collections."""
    USERS = "users"  # Legacy collection - will be deprecated
    OWNERS = "owners"  # New collection for owner users
    SITTERS = "sitter_users"  # New collection for sitter users (different from sitter profiles)
    PROFILES = "profiles"
    PETS = "pets"
    BOOKINGS = "bookings"
    SITTERS = "sitters"  # Sitter profiles/listings


collections = Collections()


class Settings(BaseSettings):
    """App settings."""
    PROJECT_NAME: str = "Waggy API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # MongoDB settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "waggy_sitters")
    
    # Debug flag
    DEBUG: bool = ENVIRONMENT == "development"
    
    # For backward compatibility
    API_V1_PREFIX: str = None
    MONGODB_DB: str = None
    
    def model_post_init(self, __context):
        """Process after model initialization."""
        # Handle backward compatibility
        if self.API_V1_PREFIX and not self.API_V1_STR:
            self.API_V1_STR = self.API_V1_PREFIX
            
        if self.MONGODB_DB and not self.MONGODB_DB_NAME:
            self.MONGODB_DB_NAME = self.MONGODB_DB
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields


settings = Settings() 
