import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # MongoDB settings
    MONGODB_URL: str
    MONGODB_DB: str
    
    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create settings instance
settings = Settings()

# MongoDB collections
class MongoCollections(BaseModel):
    USERS: str = "users"
    PROFILES: str = "profiles"
    PETS: str = "pets"
    BOOKINGS: str = "bookings"
    APPLICATIONS: str = "applications"
    MESSAGES: str = "messages"
    REVIEWS: str = "reviews"
    AVAILABILITY: str = "availability"

# Create collections instance
collections = MongoCollections() 
