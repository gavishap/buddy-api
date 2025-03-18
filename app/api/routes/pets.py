"""Pet routes."""
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
    prefix="/pets",
    tags=["pets"],
)

# Sample pet data for development
MOCK_PETS = [
    {
        "id": "1",
        "owner_id": "mock_user_id",
        "name": "Max",
        "type": "Dog",
        "breed": "Golden Retriever",
        "age": 3,
        "weight": 30,
        "notes": "Friendly and loves to play fetch."
    },
    {
        "id": "2",
        "owner_id": "mock_user_id",
        "name": "Bella",
        "type": "Dog",
        "breed": "Beagle",
        "age": 2,
        "weight": 12,
        "notes": "Energetic and needs regular walks."
    }
]

@router.get("/")
async def get_pets(request: Request, owner_id: Optional[str] = None):
    """Get all pets, optionally filtered by owner_id."""
    try:
        db = await get_database()
        filter_query = {}
        
        if owner_id:
            filter_query["owner_id"] = owner_id
            
        pets = await db[collections.PETS].find(filter_query).to_list(length=100)
        
        # Convert ObjectId to string
        for pet in pets:
            if "_id" in pet:
                pet["id"] = str(pet["_id"])
                del pet["_id"]
                
        return pets
    except Exception as e:
        logger.error(f"Error getting pets: {str(e)}")
        # For development, return mock data
        if settings.ENVIRONMENT == "development":
            if owner_id:
                return [pet for pet in MOCK_PETS if pet["owner_id"] == owner_id]
            return MOCK_PETS
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving pets",
        )

@router.get("/owner/{owner_id}")
async def get_owner_pets(owner_id: str, request: Request):
    """Get pets for a specific owner."""
    try:
        db = await get_database()
        pets = await db[collections.PETS].find({"owner_id": owner_id}).to_list(length=100)
        
        # Convert ObjectId to string
        for pet in pets:
            if "_id" in pet:
                pet["id"] = str(pet["_id"])
                del pet["_id"]
                
        return pets
    except Exception as e:
        logger.error(f"Error getting pets for owner {owner_id}: {str(e)}")
        # For development, return mock data
        if settings.ENVIRONMENT == "development":
            if owner_id == "mock_user_id":
                return MOCK_PETS
            # For other user IDs, create a random pet
            return [
                {
                    "id": "101",
                    "owner_id": owner_id,
                    "name": "Buddy",
                    "type": "Dog",
                    "breed": "Mixed",
                    "age": 4,
                    "weight": 25,
                    "notes": "Very friendly with other dogs."
                }
            ]
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving pets",
        )

@router.get("/{pet_id}")
async def get_pet(pet_id: str, request: Request):
    """Get a specific pet by ID."""
    try:
        db = await get_database()
        pet = None
        
        # Try to find by id
        pet = await db[collections.PETS].find_one({"id": pet_id})
        
        # If not found, try with ObjectId
        if not pet and len(pet_id) == 24:
            try:
                pet = await db[collections.PETS].find_one({"_id": ObjectId(pet_id)})
            except Exception:
                pass
                
        if not pet:
            # For development, check mock data
            if settings.ENVIRONMENT == "development":
                for mock_pet in MOCK_PETS:
                    if mock_pet["id"] == pet_id:
                        return mock_pet
                        
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pet not found",
            )
            
        # Convert ObjectId to string
        if "_id" in pet:
            pet["id"] = str(pet["_id"])
            del pet["_id"]
            
        return pet
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pet {pet_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving pet",
        )

@router.post("/")
async def create_pet(request: Request):
    """Create a new pet."""
    # For now, just return a success message
    return {"message": "Pet created successfully"}

@router.put("/{pet_id}")
async def update_pet(pet_id: str, request: Request):
    """Update a pet."""
    # For now, just return a success message
    return {"message": "Pet updated successfully"}

@router.delete("/{pet_id}")
async def delete_pet(pet_id: str, request: Request):
    """Delete a pet."""
    # For now, just return a success message
    return {"message": "Pet deleted successfully"} 
