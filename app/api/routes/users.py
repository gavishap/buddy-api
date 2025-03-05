"""User routes."""
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/me")
async def get_current_user():
    """Get current user info."""
    # For now, just return a mock user
    return {
        "id": "mock_user_id",
        "email": "user@example.com",
        "user_type": "owner",
    }


@router.get("/{user_id}")
async def get_user(user_id: str):
    """Get user by ID."""
    # For now, just return a mock user
    return {
        "id": user_id,
        "email": "user@example.com",
        "user_type": "owner",
    }


@router.put("/me")
async def update_user():
    """Update current user info."""
    return {"message": "User updated successfully"}


@router.delete("/me")
async def delete_user():
    """Delete current user."""
    return {"message": "User deleted successfully"} 
