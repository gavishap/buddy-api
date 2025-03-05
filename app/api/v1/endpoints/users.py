from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.api.deps import get_current_user, get_current_active_user
from app.schemas.user import User, UserUpdate
from app.db.mongodb import get_database
from app.core.security import get_password_hash
import logging

router = APIRouter()

@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve users.
    """
    db = await get_database()
    users = await db.users.find().skip(skip).limit(limit).to_list(length=limit)
    
    # Convert _id to id for each user
    for user in users:
        user["id"] = str(user.pop("_id"))
    
    return users

@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific user by id.
    """
    db = await get_database()
    
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Convert _id to id
    user["id"] = str(user.pop("_id"))
    
    return user

@router.put("/me", response_model=User)
async def update_user_me(
    user_in: UserUpdate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    db = await get_database()
    user_id = ObjectId(current_user["id"])
    
    # Prepare update data
    update_data = user_in.dict(exclude_unset=True)
    
    # If password is being updated, hash it
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # Add updated_at timestamp
    update_data["updated_at"] = None  # Will be set to current time by MongoDB
    
    try:
        # Update user
        await db.users.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        # Get updated user
        updated_user = await db.users.find_one({"_id": user_id})
        updated_user["id"] = str(updated_user.pop("_id"))
        
        return updated_user
        
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    except Exception as e:
        logging.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the user",
        )

@router.delete("/me", response_model=User)
async def delete_user_me(
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Delete own user.
    """
    db = await get_database()
    user_id = ObjectId(current_user["id"])
    
    try:
        # Delete user
        result = await db.users.delete_one({"_id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Delete user profile
        await db.profiles.delete_one({"user_id": str(user_id)})
        
        # Delete user's pets
        await db.pets.delete_many({"owner_id": str(user_id)})
        
        # Mark user's bookings as cancelled
        await db.bookings.update_many(
            {"$or": [{"owner_id": str(user_id)}, {"sitter_id": str(user_id)}]},
            {"$set": {"status": "cancelled", "updated_at": None}}
        )
        
        return current_user
        
    except Exception as e:
        logging.error(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the user",
        ) 
