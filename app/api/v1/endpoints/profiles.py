from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId

from app.api.deps import get_current_user, get_current_active_user
from app.schemas.profile import Profile, ProfileUpdate, SitterProfile, SitterProfileUpdate
from app.db.mongodb import get_database
import logging

router = APIRouter()

@router.get("/me", response_model=Profile)
async def read_profile_me(
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Get current user's profile.
    """
    db = await get_database()
    profile = await db.profiles.find_one({"user_id": current_user["id"]})
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    
    # Convert _id to id
    profile["id"] = str(profile.pop("_id"))
    
    return profile

@router.put("/me", response_model=Profile)
async def update_profile_me(
    profile_in: ProfileUpdate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Update current user's profile.
    """
    db = await get_database()
    
    # Get current profile
    profile = await db.profiles.find_one({"user_id": current_user["id"]})
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    
    # Prepare update data
    update_data = profile_in.dict(exclude_unset=True)
    update_data["updated_at"] = None  # Will be set to current time by MongoDB
    
    try:
        # Update profile
        await db.profiles.update_one(
            {"user_id": current_user["id"]},
            {"$set": update_data}
        )
        
        # Get updated profile
        updated_profile = await db.profiles.find_one({"user_id": current_user["id"]})
        updated_profile["id"] = str(updated_profile.pop("_id"))
        
        return updated_profile
        
    except Exception as e:
        logging.error(f"Error updating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the profile",
        )

@router.get("/sitters", response_model=List[SitterProfile])
async def read_sitter_profiles(
    skip: int = 0,
    limit: int = 100,
    service: Optional[str] = Query(None, description="Filter by service type"),
    min_rating: Optional[float] = Query(None, description="Filter by minimum rating"),
    max_hourly_rate: Optional[float] = Query(None, description="Filter by maximum hourly rate"),
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve sitter profiles with optional filtering.
    """
    db = await get_database()
    
    # Build query
    query = {"user_type": "sitter"}
    
    if service:
        query["services"] = service
    
    if min_rating is not None:
        query["rating"] = {"$gte": min_rating}
    
    if max_hourly_rate is not None:
        query["hourly_rate"] = {"$lte": max_hourly_rate}
    
    # Execute query
    sitters = await db.profiles.find(query).skip(skip).limit(limit).to_list(length=limit)
    
    # Convert _id to id for each sitter
    for sitter in sitters:
        sitter["id"] = str(sitter.pop("_id"))
    
    return sitters

@router.get("/sitters/{sitter_id}", response_model=SitterProfile)
async def read_sitter_profile(
    sitter_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific sitter profile by id.
    """
    db = await get_database()
    
    try:
        profile = await db.profiles.find_one({"_id": ObjectId(sitter_id), "user_type": "sitter"})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid profile ID format",
        )
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sitter profile not found",
        )
    
    # Convert _id to id
    profile["id"] = str(profile.pop("_id"))
    
    return profile

@router.put("/sitters/me", response_model=SitterProfile)
async def update_sitter_profile_me(
    profile_in: SitterProfileUpdate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Update current user's sitter profile.
    """
    db = await get_database()
    
    # Get current profile
    profile = await db.profiles.find_one({"user_id": current_user["id"]})
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    
    if profile.get("user_type") != "sitter":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a sitter",
        )
    
    # Prepare update data
    update_data = profile_in.dict(exclude_unset=True)
    update_data["updated_at"] = None  # Will be set to current time by MongoDB
    
    try:
        # Update profile
        await db.profiles.update_one(
            {"user_id": current_user["id"]},
            {"$set": update_data}
        )
        
        # Get updated profile
        updated_profile = await db.profiles.find_one({"user_id": current_user["id"]})
        updated_profile["id"] = str(updated_profile.pop("_id"))
        
        return updated_profile
        
    except Exception as e:
        logging.error(f"Error updating sitter profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the sitter profile",
        )

@router.get("/{user_id}", response_model=Profile)
async def read_user_profile(
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Get a user's profile by user ID.
    """
    db = await get_database()
    
    # Try to find the profile by user_id
    profile = await db.profiles.find_one({"user_id": user_id})
    
    # If not found, try to find by MongoDB ObjectId (for backward compatibility)
    if not profile:
        try:
            profile = await db.profiles.find_one({"_id": ObjectId(user_id)})
        except Exception:
            pass
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    
    # Convert _id to id
    profile["id"] = str(profile.pop("_id"))
    
    return profile

@router.get("/auth/{user_id}", response_model=Profile)
async def read_user_profile_auth_alias(
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Alias for /{user_id} to support the mobile app.
    Get a user's profile by user ID.
    """
    db = await get_database()
    
    # Try to find the profile by user_id
    profile = await db.profiles.find_one({"user_id": user_id})
    
    # If not found, try to find by MongoDB ObjectId (for backward compatibility)
    if not profile:
        try:
            profile = await db.profiles.find_one({"_id": ObjectId(user_id)})
        except Exception:
            pass
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    
    # Convert _id to id
    profile["id"] = str(profile.pop("_id"))
    
    return profile 
