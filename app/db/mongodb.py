from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from fastapi import HTTPException, status
import logging

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB client
client = AsyncIOMotorClient(settings.MONGODB_URL)

async def connect_to_mongo():
    """Connect to MongoDB."""
    global client
    try:
        # Verify connection
        await client.admin.command('ping')
        logger.info("Connected to MongoDB")
    except ConnectionFailure as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to database",
        )

async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        logger.info("Closed MongoDB connection")

async def get_database():
    """Get database instance."""
    return client[settings.MONGODB_DB_NAME] 
