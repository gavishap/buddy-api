from typing import Any, List, Optional
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId

from app.api.deps import get_current_user, get_current_active_user
from app.schemas.availability import (
    RecurringAvailability, RecurringAvailabilityCreate, RecurringAvailabilityUpdate,
    SpecificAvailability, SpecificAvailabilityCreate, SpecificAvailabilityUpdate,
    AvailabilityResponse
)
from app.db.mongodb import get_database
import logging

router = APIRouter()

@router.post("/recurring", response_model=RecurringAvailability)
async def create_recurring_availability(
    availability_in: RecurringAvailabilityCreate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Create a new recurring availability.
    """
    db = await get_database()
    
    # Ensure sitter_id matches current user
    if availability_in.sitter_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sitter ID must match current user ID",
        )
    
    # Verify user is a sitter
    profile = await db.profiles.find_one({"user_id": current_user["id"]})
    if not profile or profile.get("user_type") != "sitter":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a sitter",
        )
    
    # Check if availability for this day already exists
    existing = await db.recurring_availability.find_one({
        "sitter_id": current_user["id"],
        "day_of_week": availability_in.day_of_week
    })
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Recurring availability for {availability_in.day_of_week} already exists",
        )
    
    # Prepare availability data
    availability_data = availability_in.dict()
    availability_data["created_at"] = None  # Will be set to current time by MongoDB
    
    try:
        # Insert availability
        result = await db.recurring_availability.insert_one(availability_data)
        availability_id = result.inserted_id
        
        # Get created availability
        created_availability = await db.recurring_availability.find_one({"_id": availability_id})
        created_availability["id"] = str(created_availability.pop("_id"))
        
        return created_availability
        
    except Exception as e:
        logging.error(f"Error creating recurring availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the recurring availability",
        )

@router.get("/recurring", response_model=List[RecurringAvailability])
async def read_recurring_availabilities(
    sitter_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve recurring availabilities for a sitter.
    """
    db = await get_database()
    
    # Verify sitter exists
    profile = await db.profiles.find_one({"user_id": sitter_id, "user_type": "sitter"})
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sitter not found",
        )
    
    # Execute query
    availabilities = await db.recurring_availability.find({"sitter_id": sitter_id}).to_list(length=100)
    
    # Convert _id to id for each availability
    for availability in availabilities:
        availability["id"] = str(availability.pop("_id"))
    
    return availabilities

@router.put("/recurring/{availability_id}", response_model=RecurringAvailability)
async def update_recurring_availability(
    availability_id: str,
    availability_in: RecurringAvailabilityUpdate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Update a recurring availability.
    """
    db = await get_database()
    
    try:
        availability = await db.recurring_availability.find_one({"_id": ObjectId(availability_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid availability ID format",
        )
    
    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring availability not found",
        )
    
    # Check if current user is the sitter
    if availability["sitter_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Prepare update data
    update_data = availability_in.dict(exclude_unset=True)
    update_data["updated_at"] = None  # Will be set to current time by MongoDB
    
    try:
        # Update availability
        await db.recurring_availability.update_one(
            {"_id": ObjectId(availability_id)},
            {"$set": update_data}
        )
        
        # Get updated availability
        updated_availability = await db.recurring_availability.find_one({"_id": ObjectId(availability_id)})
        updated_availability["id"] = str(updated_availability.pop("_id"))
        
        return updated_availability
        
    except Exception as e:
        logging.error(f"Error updating recurring availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the recurring availability",
        )

@router.delete("/recurring/{availability_id}", response_model=RecurringAvailability)
async def delete_recurring_availability(
    availability_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Delete a recurring availability.
    """
    db = await get_database()
    
    try:
        availability = await db.recurring_availability.find_one({"_id": ObjectId(availability_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid availability ID format",
        )
    
    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring availability not found",
        )
    
    # Check if current user is the sitter
    if availability["sitter_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    try:
        # Delete availability
        result = await db.recurring_availability.delete_one({"_id": ObjectId(availability_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recurring availability not found",
            )
        
        # Convert _id to id for response
        availability["id"] = str(availability.pop("_id"))
        
        return availability
        
    except Exception as e:
        logging.error(f"Error deleting recurring availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the recurring availability",
        )

@router.post("/specific", response_model=SpecificAvailability)
async def create_specific_availability(
    availability_in: SpecificAvailabilityCreate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Create a new specific availability.
    """
    db = await get_database()
    
    # Ensure sitter_id matches current user
    if availability_in.sitter_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sitter ID must match current user ID",
        )
    
    # Verify user is a sitter
    profile = await db.profiles.find_one({"user_id": current_user["id"]})
    if not profile or profile.get("user_type") != "sitter":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a sitter",
        )
    
    # Check if availability for this date already exists
    existing = await db.specific_availability.find_one({
        "sitter_id": current_user["id"],
        "date": availability_in.date
    })
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Specific availability for {availability_in.date} already exists",
        )
    
    # Prepare availability data
    availability_data = availability_in.dict()
    availability_data["created_at"] = None  # Will be set to current time by MongoDB
    
    try:
        # Insert availability
        result = await db.specific_availability.insert_one(availability_data)
        availability_id = result.inserted_id
        
        # Get created availability
        created_availability = await db.specific_availability.find_one({"_id": availability_id})
        created_availability["id"] = str(created_availability.pop("_id"))
        
        return created_availability
        
    except Exception as e:
        logging.error(f"Error creating specific availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the specific availability",
        )

@router.get("/specific", response_model=List[SpecificAvailability])
async def read_specific_availabilities(
    sitter_id: str,
    start_date: date = Query(..., description="Start date for availability range"),
    end_date: date = Query(..., description="End date for availability range"),
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve specific availabilities for a sitter within a date range.
    """
    db = await get_database()
    
    # Verify sitter exists
    profile = await db.profiles.find_one({"user_id": sitter_id, "user_type": "sitter"})
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sitter not found",
        )
    
    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date",
        )
    
    # Limit range to 30 days
    if (end_date - start_date).days > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 30 days",
        )
    
    # Execute query
    availabilities = await db.specific_availability.find({
        "sitter_id": sitter_id,
        "date": {"$gte": start_date, "$lte": end_date}
    }).to_list(length=100)
    
    # Convert _id to id for each availability
    for availability in availabilities:
        availability["id"] = str(availability.pop("_id"))
    
    return availabilities

@router.put("/specific/{availability_id}", response_model=SpecificAvailability)
async def update_specific_availability(
    availability_id: str,
    availability_in: SpecificAvailabilityUpdate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Update a specific availability.
    """
    db = await get_database()
    
    try:
        availability = await db.specific_availability.find_one({"_id": ObjectId(availability_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid availability ID format",
        )
    
    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specific availability not found",
        )
    
    # Check if current user is the sitter
    if availability["sitter_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Prepare update data
    update_data = availability_in.dict(exclude_unset=True)
    update_data["updated_at"] = None  # Will be set to current time by MongoDB
    
    try:
        # Update availability
        await db.specific_availability.update_one(
            {"_id": ObjectId(availability_id)},
            {"$set": update_data}
        )
        
        # Get updated availability
        updated_availability = await db.specific_availability.find_one({"_id": ObjectId(availability_id)})
        updated_availability["id"] = str(updated_availability.pop("_id"))
        
        return updated_availability
        
    except Exception as e:
        logging.error(f"Error updating specific availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the specific availability",
        )

@router.delete("/specific/{availability_id}", response_model=SpecificAvailability)
async def delete_specific_availability(
    availability_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Delete a specific availability.
    """
    db = await get_database()
    
    try:
        availability = await db.specific_availability.find_one({"_id": ObjectId(availability_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid availability ID format",
        )
    
    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specific availability not found",
        )
    
    # Check if current user is the sitter
    if availability["sitter_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    try:
        # Delete availability
        result = await db.specific_availability.delete_one({"_id": ObjectId(availability_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specific availability not found",
            )
        
        # Convert _id to id for response
        availability["id"] = str(availability.pop("_id"))
        
        return availability
        
    except Exception as e:
        logging.error(f"Error deleting specific availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the specific availability",
        )

@router.get("/{sitter_id}", response_model=AvailabilityResponse)
async def get_sitter_availability(
    sitter_id: str,
    start_date: date = Query(..., description="Start date for availability range"),
    end_date: date = Query(..., description="End date for availability range"),
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Get combined recurring and specific availability for a sitter.
    """
    db = await get_database()
    
    # Verify sitter exists
    profile = await db.profiles.find_one({"user_id": sitter_id, "user_type": "sitter"})
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sitter not found",
        )
    
    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date",
        )
    
    # Limit range to 30 days
    if (end_date - start_date).days > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 30 days",
        )
    
    # Get recurring availabilities
    recurring = await db.recurring_availability.find({"sitter_id": sitter_id}).to_list(length=100)
    for availability in recurring:
        availability["id"] = str(availability.pop("_id"))
    
    # Get specific availabilities
    specific = await db.specific_availability.find({
        "sitter_id": sitter_id,
        "date": {"$gte": start_date, "$lte": end_date}
    }).to_list(length=100)
    for availability in specific:
        availability["id"] = str(availability.pop("_id"))
    
    return {
        "recurring": recurring,
        "specific": specific
    } 
