"""Booking routes."""
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
)


@router.get("/owner")
async def get_owner_bookings():
    """Get all bookings for the current owner."""
    # For now, just return mock bookings
    return [
        {
            "id": "booking1",
            "owner_id": "mock_user_id",
            "sitter_id": "sitter1",
            "pet_id": "pet1",
            "service": "Dog Walking",
            "start_time": "2024-03-10T10:00:00",
            "end_time": "2024-03-10T11:00:00",
            "status": "confirmed",
            "price": 25.0,
        },
        {
            "id": "booking2",
            "owner_id": "mock_user_id",
            "sitter_id": "sitter2",
            "pet_id": "pet2",
            "service": "Overnight Care",
            "start_time": "2024-03-15T18:00:00",
            "end_time": "2024-03-16T08:00:00",
            "status": "pending",
            "price": 85.0,
        },
    ]


@router.get("/sitter")
async def get_sitter_bookings():
    """Get all bookings for the current sitter."""
    # For now, just return mock bookings
    return [
        {
            "id": "booking3",
            "owner_id": "owner1",
            "sitter_id": "mock_user_id",
            "pet_id": "pet3",
            "service": "Dog Walking",
            "start_time": "2024-03-11T15:00:00",
            "end_time": "2024-03-11T16:00:00",
            "status": "confirmed",
            "price": 25.0,
        },
    ]


@router.post("/")
async def create_booking():
    """Create a new booking request."""
    return {"message": "Booking created successfully", "booking_id": "new_booking_id"}


@router.get("/{booking_id}")
async def get_booking(booking_id: str):
    """Get a specific booking by ID."""
    return {
        "id": booking_id,
        "owner_id": "mock_user_id",
        "sitter_id": "sitter1",
        "pet_id": "pet1",
        "service": "Dog Walking",
        "start_time": "2024-03-10T10:00:00",
        "end_time": "2024-03-10T11:00:00",
        "status": "confirmed",
        "price": 25.0,
    }


@router.put("/{booking_id}")
async def update_booking(booking_id: str):
    """Update a booking."""
    return {"message": f"Booking {booking_id} updated successfully"}


@router.patch("/{booking_id}/status")
async def update_booking_status(booking_id: str):
    """Update a booking status (confirm, reject, cancel)."""
    return {"message": f"Booking {booking_id} status updated successfully"}


@router.delete("/{booking_id}")
async def delete_booking(booking_id: str):
    """Delete a booking."""
    return {"message": f"Booking {booking_id} deleted successfully"} 
