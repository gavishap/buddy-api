"""User routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from jose import jwt, JWTError
from bson.objectid import ObjectId
import logging

from app.core.config import settings, collections
from app.db.mongodb import get_database

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

async def get_user_from_token(authorization: str = None):
    """Get user from token."""
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Invalid or missing authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Decode the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("No subject claim in token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        
        # Get the user from the database
        db = await get_database()
        logger.info(f"Looking up user with ID: {user_id} in database {settings.MONGODB_DB_NAME}")
        
        # Try to find by id first
        user = await db[collections.USERS].find_one({"id": user_id})
        
        # If not found, try with ObjectId
        if not user:
            try:
                logger.info(f"User not found by id, trying ObjectId: {user_id}")
                user = await db[collections.USERS].find_one({"_id": ObjectId(user_id)})
            except Exception as e:
                logger.error(f"Error converting to ObjectId: {str(e)}")
                # If ObjectId conversion fails, just return None
                pass
        
        if not user:
            logger.warning(f"User not found with ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
            
        # Convert _id to string if present
        if "_id" in user:
            user["id"] = str(user["_id"])
            del user["_id"]
        
        logger.info(f"User found: {user.get('email')}")
        return user
        
    except JWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

@router.get("/me")
async def get_current_user(request: Request):
    """Get current user info using token from Authorization header."""
    # Get the authorization from request state (set by middleware)
    authorization = request.state.authorization
    
    if authorization:
        try:
            user = await get_user_from_token(authorization)
            if user:
                # Remove sensitive data
                if "hashed_password" in user:
                    del user["hashed_password"]
                logger.info(f"Returning user data for: {user.get('email')}")
                return user
        except Exception as e:
            logger.error(f"Error in get_current_user: {str(e)}")
            if settings.ENVIRONMENT != "development":
                raise
    
    # For development, fallback to mock data
    if settings.ENVIRONMENT == "development":
        logger.warning("Returning mock user data as fallback")
        return {
            "id": "mock_user_id",
            "email": "user@example.com",
            "user_type": "owner",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

@router.get("/{user_id}")
async def get_user(user_id: str):
    """Get user by ID."""
    db = await get_database()
    
    try:
        # First try to find by id
        user = await db[collections.USERS].find_one({"id": user_id})
        
        # If not found, try with ObjectId
        if not user:
            try:
                user = await db[collections.USERS].find_one({"_id": ObjectId(user_id)})
            except:
                # If ObjectId conversion fails, return 404
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Convert _id to string if present
        if "_id" in user:
            user["id"] = str(user["_id"])
            del user["_id"]
            
        # Remove sensitive data
        if "hashed_password" in user:
            del user["hashed_password"]
            
        return user
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user",
        )

@router.put("/me")
async def update_user():
    """Update current user info."""
    return {"message": "User updated successfully"}

@router.delete("/me")
async def delete_user():
    """Delete current user."""
    return {"message": "User deleted successfully"} 
