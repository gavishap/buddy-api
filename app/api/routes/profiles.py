"""Profile routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from bson import ObjectId
import logging
from datetime import datetime

from app.core.config import settings, collections
from app.db.mongodb import get_database

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/profiles",
    tags=["profiles"],
)


@router.get("/owner/me")
async def get_owner_profile():
    """Get current owner's profile."""
    # For now, just return a mock profile
    return {
        "id": "mock_profile_id",
        "user_id": "mock_user_id",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "123-456-7890",
        "address": "123 Main St",
        "bio": "Pet lover",
    }


@router.get("/sitter/me")
async def get_sitter_profile():
    """Get current sitter's profile."""
    # For now, just return a mock profile
    return {
        "id": "mock_profile_id",
        "user_id": "mock_user_id",
        "first_name": "Jane",
        "last_name": "Smith",
        "phone": "123-456-7890",
        "bio": "Professional pet sitter",
        "services": ["dog walking", "overnight care"],
        "rate": 25.0,
        "availability": ["weekdays", "weekends"],
    }


@router.put("/owner/me")
async def update_owner_profile():
    """Update current owner's profile."""
    return {"message": "Owner profile updated successfully"}


@router.put("/sitter/me")
async def update_sitter_profile():
    """Update current sitter's profile."""
    return {"message": "Sitter profile updated successfully"}


@router.get("/{user_id}")
async def get_profile(user_id: str, request: Request):
    """Get user profile by user ID."""
    db = await get_database()
    logger.info(f"Looking up profile for user ID: {user_id}")
    
    try:
        # First try to find profile by user_id
        profile = await db[collections.PROFILES].find_one({"user_id": user_id})
        
        # If not found and user_id looks like an ObjectId, try with that
        if not profile and len(user_id) == 24:
            try:
                # Try to find user first to get their ID field (which might be different from _id)
                user = await db[collections.USERS].find_one({"_id": ObjectId(user_id)})
                if user:
                    actual_id = user.get("id", str(user.get("_id")))
                    logger.info(f"Found user, looking up profile with user_id: {actual_id}")
                    profile = await db[collections.PROFILES].find_one({"user_id": actual_id})
            except Exception as e:
                logger.error(f"Error finding user with ObjectId: {str(e)}")
        
        # If still no profile, use the user data as the profile
        if not profile:
            logger.info(f"No profile found, using user data as profile")
            try:
                # Try by id first
                user = await db[collections.USERS].find_one({"id": user_id})
                # Then try by ObjectId
                if not user and len(user_id) == 24:
                    try:
                        user = await db[collections.USERS].find_one({"_id": ObjectId(user_id)})
                    except Exception as e:
                        logger.error(f"Error finding user with ObjectId: {str(e)}")
                
                if user:
                    # Create a profile from user data
                    profile = {
                        "id": str(ObjectId()),  # Generate a new ID for the profile
                        "user_id": user_id,
                        "email": user.get("email"),
                        "first_name": user.get("first_name") or "",
                        "last_name": user.get("last_name") or "",
                        "user_type": user.get("user_type", "owner"),
                        "created_at": user.get("created_at", datetime.utcnow().isoformat()),
                    }
                    
                    # Store this profile for future use
                    result = await db[collections.PROFILES].insert_one(profile)
                    profile["id"] = str(result.inserted_id)
                    logger.info(f"Created new profile for user: {user_id}")
            except Exception as e:
                logger.error(f"Error creating profile from user data: {str(e)}")
        
        if not profile:
            # If still no profile, return 404
            logger.warning(f"No profile or user found for ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )
        
        # Convert _id to string if present
        if "_id" in profile:
            profile["id"] = str(profile["_id"])
            del profile["_id"]
            
        return profile
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving profile for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving profile",
        )


@router.put("/{user_id}")
async def update_profile(user_id: str, request: Request):
    """Update user profile."""
    return {"message": "Profile updated successfully"}


@router.post("/")
async def create_profile(request: Request):
    """Create a new profile."""
    return {"message": "Profile created successfully"} 
