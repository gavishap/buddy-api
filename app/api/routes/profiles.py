"""Profile routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from bson import ObjectId
import logging
from datetime import datetime
from jose import jwt

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
    
    # Extract user_type from authorization token if available
    user_type = None
    authorization = request.state.authorization
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_type = payload.get("user_type")
            logger.info(f"Extracted user_type from token: {user_type}")
        except Exception as e:
            logger.warning(f"Could not extract user_type from token: {str(e)}")
    
    try:
        user_profile = None
        
        # If we know the user type from the token, check that collection first
        if user_type == "owner":
            logger.info(f"Checking owners collection first based on token")
            try:
                user_profile = await db[collections.OWNERS].find_one({"_id": ObjectId(user_id)})
            except Exception as e:
                logger.error(f"Error finding owner with ID {user_id}: {str(e)}")
                
        elif user_type == "sitter":
            logger.info(f"Checking sitters collection first based on token")
            try:
                user_profile = await db[collections.SITTERS].find_one({"_id": ObjectId(user_id)})
            except Exception as e:
                logger.error(f"Error finding sitter with ID {user_id}: {str(e)}")
        
        # If user_profile is still None, try all collections
        if not user_profile:
            logger.info(f"No profile found with known user type, trying all collections")
            
            # Try owners collection
            try:
                user_profile = await db[collections.OWNERS].find_one({"_id": ObjectId(user_id)})
                if user_profile:
                    logger.info(f"Found profile in owners collection")
                    user_type = "owner"
            except Exception as e:
                logger.error(f"Error checking owners collection: {str(e)}")
            
            # If not found, try sitters collection
            if not user_profile:
                try:
                    user_profile = await db[collections.SITTERS].find_one({"_id": ObjectId(user_id)})
                    if user_profile:
                        logger.info(f"Found profile in sitters collection")
                        user_type = "sitter"
                except Exception as e:
                    logger.error(f"Error checking sitters collection: {str(e)}")
            
            # If still not found, try legacy users collection as last resort
            if not user_profile:
                try:
                    user_profile = await db[collections.USERS].find_one({"_id": ObjectId(user_id)})
                    if user_profile:
                        logger.info(f"Found profile in legacy users collection")
                        user_type = user_profile.get("user_type", "owner")
                except Exception as e:
                    logger.error(f"Error checking legacy users collection: {str(e)}")
        
        if not user_profile:
            # If user is not found in any collection, return 404
            logger.warning(f"No profile found for ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )
        
        # Convert _id to string if present and ensure user_type is set
        if "_id" in user_profile:
            user_profile["id"] = str(user_profile["_id"])
            del user_profile["_id"]
        
        # Make sure user_type is set
        if "user_type" not in user_profile:
            user_profile["user_type"] = user_type or "owner"
            
        # Remove sensitive data
        if "hashed_password" in user_profile:
            del user_profile["hashed_password"]
        
        logger.info(f"Returning profile data for user ID: {user_id}, type: {user_profile.get('user_type')}")
        return user_profile
        
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
    # Get the request data
    try:
        profile_data = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON: {str(e)}",
        )
    
    # Extract user_type from authorization token
    user_type = None
    authorization = request.state.authorization
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_type = payload.get("user_type")
            logger.info(f"Extracted user_type from token: {user_type}")
        except Exception as e:
            logger.warning(f"Could not extract user_type from token: {str(e)}")
    
    db = await get_database()
    
    # Determine which collection to update based on user_type
    collection_name = None
    if user_type == "owner":
        collection_name = collections.OWNERS
    elif user_type == "sitter":
        collection_name = collections.SITTERS
    else:
        # If user_type not known, check all collections
        try:
            owner = await db[collections.OWNERS].find_one({"_id": ObjectId(user_id)})
            if owner:
                collection_name = collections.OWNERS
                user_type = "owner"
        except Exception:
            pass
        
        if not collection_name:
            try:
                sitter = await db[collections.SITTERS].find_one({"_id": ObjectId(user_id)})
                if sitter:
                    collection_name = collections.SITTERS
                    user_type = "sitter"
            except Exception:
                pass
        
        if not collection_name:
            # Last resort, check legacy users
            try:
                user = await db[collections.USERS].find_one({"_id": ObjectId(user_id)})
                if user:
                    collection_name = collections.USERS
                    user_type = user.get("user_type", "owner")
            except Exception:
                pass
    
    if not collection_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Remove any fields that shouldn't be updated
    for field in ["id", "_id", "email", "hashed_password", "user_type", "created_at"]:
        if field in profile_data:
            del profile_data[field]
    
    # Update the profile
    try:
        result = await db[collection_name].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": profile_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
            
        # Get the updated profile
        updated_profile = await db[collection_name].find_one({"_id": ObjectId(user_id)})
        
        # Clean up before returning
        if "_id" in updated_profile:
            updated_profile["id"] = str(updated_profile["_id"])
            del updated_profile["_id"]
        
        if "hashed_password" in updated_profile:
            del updated_profile["hashed_password"]
        
        return updated_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}",
        )


@router.post("/")
async def create_profile(request: Request):
    """Create a new profile."""
    return {"message": "Profile created successfully"} 
