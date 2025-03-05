"""Profile routes."""
from fastapi import APIRouter, Depends, HTTPException, status

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
