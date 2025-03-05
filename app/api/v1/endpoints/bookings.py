from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId

from app.api.deps import get_current_user, get_current_active_user
from app.schemas.booking import Booking, BookingCreate, BookingUpdate, BookingWithDetails, BookingStatus
from app.db.mongodb import get_database
import logging

router = APIRouter()

@router.post("/", response_model=Booking)
async def create_booking(
    booking_in: BookingCreate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Create a new booking.
    """
    db = await get_database()
    
    # Ensure owner_id matches current user
    if booking_in.owner_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner ID must match current user ID",
        )
    
    # Verify sitter exists
    sitter = await db.profiles.find_one({"user_id": booking_in.sitter_id, "user_type": "sitter"})
    if not sitter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sitter not found",
        )
    
    # Verify all pets exist and belong to the owner
    for pet_id in booking_in.pet_ids:
        try:
            pet = await db.pets.find_one({"_id": ObjectId(pet_id)})
            if not pet or pet["owner_id"] != current_user["id"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Pet with ID {pet_id} not found or does not belong to you",
                )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid pet ID format: {pet_id}",
            )
    
    # Calculate total price based on sitter's hourly rate and booking duration
    total_price = None
    if sitter.get("hourly_rate"):
        # Calculate days between start and end date
        days = (booking_in.end_date - booking_in.start_date).days + 1
        hours_per_day = 8  # Default hours per day
        
        # If specific times are provided, calculate exact hours
        if booking_in.start_time and booking_in.end_time:
            start_datetime = datetime.combine(booking_in.start_date, booking_in.start_time)
            end_datetime = datetime.combine(booking_in.end_date, booking_in.end_time)
            hours = (end_datetime - start_datetime).total_seconds() / 3600
            total_price = hours * sitter["hourly_rate"]
        else:
            total_price = days * hours_per_day * sitter["hourly_rate"]
    
    # Prepare booking data
    booking_data = booking_in.dict()
    booking_data["created_at"] = None  # Will be set to current time by MongoDB
    
    if total_price:
        booking_data["total_price"] = round(total_price, 2)
    
    try:
        # Insert booking
        result = await db.bookings.insert_one(booking_data)
        booking_id = result.inserted_id
        
        # Get created booking
        created_booking = await db.bookings.find_one({"_id": booking_id})
        created_booking["id"] = str(created_booking.pop("_id"))
        
        return created_booking
        
    except Exception as e:
        logging.error(f"Error creating booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the booking",
        )

@router.get("/", response_model=List[Booking])
async def read_bookings(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="Filter by booking status"),
    as_owner: Optional[bool] = Query(True, description="Get bookings as owner or sitter"),
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve bookings for the current user.
    """
    db = await get_database()
    
    # Build query
    if as_owner:
        query = {"owner_id": current_user["id"]}
    else:
        query = {"sitter_id": current_user["id"]}
    
    if status:
        query["status"] = status
    
    # Execute query
    bookings = await db.bookings.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    # Convert _id to id for each booking
    for booking in bookings:
        booking["id"] = str(booking.pop("_id"))
    
    return bookings

@router.get("/{booking_id}", response_model=BookingWithDetails)
async def read_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific booking by id with detailed information.
    """
    db = await get_database()
    
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid booking ID format",
        )
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    # Check if current user is the owner or sitter
    if booking["owner_id"] != current_user["id"] and booking["sitter_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Convert _id to id
    booking["id"] = str(booking.pop("_id"))
    
    # Get owner details
    owner = await db.profiles.find_one({"user_id": booking["owner_id"]})
    if owner:
        owner["id"] = str(owner.pop("_id"))
        booking["owner"] = owner
    else:
        booking["owner"] = {"user_id": booking["owner_id"]}
    
    # Get sitter details
    sitter = await db.profiles.find_one({"user_id": booking["sitter_id"]})
    if sitter:
        sitter["id"] = str(sitter.pop("_id"))
        booking["sitter"] = sitter
    else:
        booking["sitter"] = {"user_id": booking["sitter_id"]}
    
    # Get pet details
    pets = []
    for pet_id in booking["pet_ids"]:
        try:
            pet = await db.pets.find_one({"_id": ObjectId(pet_id)})
            if pet:
                pet["id"] = str(pet.pop("_id"))
                pets.append(pet)
            else:
                pets.append({"id": pet_id, "name": "Unknown Pet"})
        except Exception:
            pets.append({"id": pet_id, "name": "Unknown Pet"})
    
    booking["pets"] = pets
    
    return booking

@router.put("/{booking_id}", response_model=Booking)
async def update_booking(
    booking_id: str,
    booking_in: BookingUpdate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Update a booking.
    """
    db = await get_database()
    
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid booking ID format",
        )
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    # Check permissions based on the update
    is_owner = booking["owner_id"] == current_user["id"]
    is_sitter = booking["sitter_id"] == current_user["id"]
    
    if not (is_owner or is_sitter):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Prepare update data
    update_data = booking_in.dict(exclude_unset=True)
    
    # Validate status changes
    if "status" in update_data:
        current_status = booking["status"]
        new_status = update_data["status"]
        
        # Owner can cancel a booking
        if is_owner and new_status == "cancelled" and current_status in ["pending", "confirmed"]:
            pass
        # Sitter can confirm, reject, or complete a booking
        elif is_sitter and new_status == "confirmed" and current_status == "pending":
            pass
        elif is_sitter and new_status == "rejected" and current_status == "pending":
            pass
        elif is_sitter and new_status == "completed" and current_status == "confirmed":
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {current_status} to {new_status}",
            )
    
    # Owners can update details only if booking is pending
    if is_owner and not is_sitter and booking["status"] != "pending" and any(k in update_data for k in ["start_date", "end_date", "start_time", "end_time", "pet_ids"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update booking details after it has been confirmed",
        )
    
    # Verify all pets exist and belong to the owner if pet_ids is being updated
    if "pet_ids" in update_data and is_owner:
        for pet_id in update_data["pet_ids"]:
            try:
                pet = await db.pets.find_one({"_id": ObjectId(pet_id)})
                if not pet or pet["owner_id"] != current_user["id"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Pet with ID {pet_id} not found or does not belong to you",
                    )
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid pet ID format: {pet_id}",
                )
    
    update_data["updated_at"] = None  # Will be set to current time by MongoDB
    
    try:
        # Update booking
        await db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": update_data}
        )
        
        # Get updated booking
        updated_booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
        updated_booking["id"] = str(updated_booking.pop("_id"))
        
        return updated_booking
        
    except Exception as e:
        logging.error(f"Error updating booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the booking",
        )

@router.delete("/{booking_id}", response_model=Booking)
async def delete_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Delete a booking (only if it's in pending status).
    """
    db = await get_database()
    
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid booking ID format",
        )
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    # Check if current user is the owner
    if booking["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Check if booking is in pending status
    if booking["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending bookings can be deleted",
        )
    
    try:
        # Delete booking
        result = await db.bookings.delete_one({"_id": ObjectId(booking_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )
        
        # Convert _id to id for response
        booking["id"] = str(booking.pop("_id"))
        
        return booking
        
    except Exception as e:
        logging.error(f"Error deleting booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the booking",
        ) 
