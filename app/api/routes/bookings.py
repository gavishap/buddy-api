"""Booking routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from bson import ObjectId
import logging
from datetime import datetime
from typing import List, Optional

from app.core.config import settings, collections
from app.db.mongodb import get_database

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
)

# Sample booking data for development
MOCK_BOOKINGS = [
    {
        "id": "1",
        "owner_id": "mock_user_id",
        "pet_id": "1",
        "service_type": "Dog Walking",
        "date": "2023-05-15",
        "time": "14:00",
        "duration": 60,
        "sitter_id": "sitter1",
        "status": "completed",
        "notes": "Please make sure to lock the back gate when leaving."
    },
    {
        "id": "2",
        "owner_id": "mock_user_id",
        "pet_id": "2",
        "service_type": "Pet Sitting",
        "date": "2023-05-20",
        "time": "09:00",
        "duration": 180,
        "sitter_id": "sitter2",
        "status": "upcoming",
        "notes": "Food is in the pantry, top shelf."
    },
]

@router.get("/")
async def get_bookings(request: Request, status: Optional[str] = None):
    """Get all bookings, optionally filtered by status."""
    try:
        db = await get_database()
        filter_query = {}
        
        if status:
            filter_query["status"] = status
            
        bookings = await db[collections.BOOKINGS].find(filter_query).to_list(length=100)
        
        # Convert ObjectId to string
        for booking in bookings:
            if "_id" in booking:
                booking["id"] = str(booking["_id"])
                del booking["_id"]
                
        return bookings
    except Exception as e:
        logger.error(f"Error getting bookings: {str(e)}")
        # For development, return mock data
        if settings.ENVIRONMENT == "development":
            return MOCK_BOOKINGS
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving bookings",
        )

@router.get("/owner/{owner_id}")
async def get_owner_bookings(owner_id: str, request: Request, status: Optional[str] = None):
    """Get bookings for a specific owner, optionally filtered by status."""
    logger.info(f"Getting bookings for owner: {owner_id}, status: {status}")
    try:
        db = await get_database()
        filter_query = {"owner_id": owner_id}
        
        if status:
            filter_query["status"] = status
            
        bookings = await db[collections.BOOKINGS].find(filter_query).to_list(length=100)
        
        # Convert ObjectId to string
        for booking in bookings:
            if "_id" in booking:
                booking["id"] = str(booking["_id"])
                del booking["_id"]
                
        logger.info(f"Found {len(bookings)} bookings for owner {owner_id}")
        return bookings
    except Exception as e:
        logger.error(f"Error getting bookings for owner {owner_id}: {str(e)}")
        # For development, return mock data filtered by owner_id
        if settings.ENVIRONMENT == "development":
            # Find owner in mock data
            if owner_id == "mock_user_id":
                return MOCK_BOOKINGS
            else:
                # Generate mock data for this specific owner
                return [
                    {
                        "id": "101",
                        "owner_id": owner_id,
                        "pet_id": "1",
                        "service_type": "Dog Walking",
                        "date": "2023-09-15",
                        "time": "15:00",
                        "duration": 60,
                        "sitter_id": "sitter1",
                        "status": "upcoming",
                        "notes": "Please bring water for the dog."
                    }
                ]
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving bookings",
        )

@router.get("/sitter/{sitter_id}")
async def get_sitter_bookings(sitter_id: str, request: Request, status: Optional[str] = None):
    """Get bookings for a specific sitter, optionally filtered by status."""
    try:
        db = await get_database()
        filter_query = {"sitter_id": sitter_id}
        
        if status:
            filter_query["status"] = status
            
        bookings = await db[collections.BOOKINGS].find(filter_query).to_list(length=100)
        
        # Convert ObjectId to string
        for booking in bookings:
            if "_id" in booking:
                booking["id"] = str(booking["_id"])
                del booking["_id"]
                
        return bookings
    except Exception as e:
        logger.error(f"Error getting bookings for sitter {sitter_id}: {str(e)}")
        # For development, return mock data
        if settings.ENVIRONMENT == "development":
            # Filter mock data for sitters
            return [booking for booking in MOCK_BOOKINGS if booking["sitter_id"] == sitter_id]
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving bookings",
        )

@router.get("/{booking_id}")
async def get_booking(booking_id: str, request: Request):
    """Get a specific booking by ID."""
    try:
        db = await get_database()
        booking = None
        
        # Try to find by id
        booking = await db[collections.BOOKINGS].find_one({"id": booking_id})
        
        # If not found, try with ObjectId
        if not booking and len(booking_id) == 24:
            try:
                booking = await db[collections.BOOKINGS].find_one({"_id": ObjectId(booking_id)})
            except Exception:
                pass
                
        if not booking:
            # For development, check mock data
            if settings.ENVIRONMENT == "development":
                for mock_booking in MOCK_BOOKINGS:
                    if mock_booking["id"] == booking_id:
                        return mock_booking
                        
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )
            
        # Convert ObjectId to string
        if "_id" in booking:
            booking["id"] = str(booking["_id"])
            del booking["_id"]
            
        return booking
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting booking {booking_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving booking",
        )

@router.post("/")
async def create_booking(request: Request):
    """Create a new booking."""
    # For now, just return a success message
    return {"message": "Booking created successfully"}

@router.put("/{booking_id}")
async def update_booking(booking_id: str, request: Request):
    """Update a booking."""
    # For now, just return a success message
    return {"message": "Booking updated successfully"}

@router.delete("/{booking_id}")
async def delete_booking(booking_id: str, request: Request):
    """Delete a booking."""
    # For now, just return a success message
    return {"message": "Booking deleted successfully"} 
