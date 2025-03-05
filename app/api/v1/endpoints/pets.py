from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from app.api.deps import get_current_user, get_current_active_user
from app.schemas.pet import Pet, PetCreate, PetUpdate, PetWithOwner
from app.db.mongodb import get_database
import logging

router = APIRouter()

@router.post("/", response_model=Pet)
async def create_pet(
    pet_in: PetCreate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Create a new pet.
    """
    db = await get_database()
    
    # Ensure owner_id matches current user
    if pet_in.owner_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner ID must match current user ID",
        )
    
    # Prepare pet data
    pet_data = pet_in.dict()
    pet_data["created_at"] = None  # Will be set to current time by MongoDB
    
    try:
        # Insert pet
        result = await db.pets.insert_one(pet_data)
        pet_id = result.inserted_id
        
        # Get created pet
        created_pet = await db.pets.find_one({"_id": pet_id})
        created_pet["id"] = str(created_pet.pop("_id"))
        
        return created_pet
        
    except Exception as e:
        logging.error(f"Error creating pet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the pet",
        )

@router.get("/", response_model=List[Pet])
async def read_pets(
    skip: int = 0,
    limit: int = 100,
    species: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve pets owned by current user.
    """
    db = await get_database()
    
    # Build query
    query = {"owner_id": current_user["id"]}
    
    if species:
        query["species"] = species
    
    # Execute query
    pets = await db.pets.find(query).skip(skip).limit(limit).to_list(length=limit)
    
    # Convert _id to id for each pet
    for pet in pets:
        pet["id"] = str(pet.pop("_id"))
    
    return pets

@router.get("/{pet_id}", response_model=Pet)
async def read_pet(
    pet_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific pet by id.
    """
    db = await get_database()
    
    try:
        pet = await db.pets.find_one({"_id": ObjectId(pet_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pet ID format",
        )
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found",
        )
    
    # Check if current user is the owner
    if pet["owner_id"] != current_user["id"]:
        # Check if current user is a sitter with an active booking for this pet
        is_sitter = await db.profiles.find_one({"user_id": current_user["id"], "user_type": "sitter"})
        if not is_sitter:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        
        # Check if sitter has an active booking with this pet
        booking = await db.bookings.find_one({
            "sitter_id": current_user["id"],
            "pet_ids": pet_id,
            "status": {"$in": ["confirmed", "pending"]}
        })
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    # Convert _id to id
    pet["id"] = str(pet.pop("_id"))
    
    return pet

@router.put("/{pet_id}", response_model=Pet)
async def update_pet(
    pet_id: str,
    pet_in: PetUpdate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Update a pet.
    """
    db = await get_database()
    
    try:
        pet = await db.pets.find_one({"_id": ObjectId(pet_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pet ID format",
        )
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found",
        )
    
    # Check if current user is the owner
    if pet["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Prepare update data
    update_data = pet_in.dict(exclude_unset=True)
    update_data["updated_at"] = None  # Will be set to current time by MongoDB
    
    try:
        # Update pet
        await db.pets.update_one(
            {"_id": ObjectId(pet_id)},
            {"$set": update_data}
        )
        
        # Get updated pet
        updated_pet = await db.pets.find_one({"_id": ObjectId(pet_id)})
        updated_pet["id"] = str(updated_pet.pop("_id"))
        
        return updated_pet
        
    except Exception as e:
        logging.error(f"Error updating pet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the pet",
        )

@router.delete("/{pet_id}", response_model=Pet)
async def delete_pet(
    pet_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Delete a pet.
    """
    db = await get_database()
    
    try:
        pet = await db.pets.find_one({"_id": ObjectId(pet_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pet ID format",
        )
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found",
        )
    
    # Check if current user is the owner
    if pet["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Check if pet is in any active bookings
    active_booking = await db.bookings.find_one({
        "pet_ids": pet_id,
        "status": {"$in": ["confirmed", "pending"]}
    })
    
    if active_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete pet with active bookings",
        )
    
    try:
        # Delete pet
        result = await db.pets.delete_one({"_id": ObjectId(pet_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pet not found",
            )
        
        # Convert _id to id for response
        pet["id"] = str(pet.pop("_id"))
        
        return pet
        
    except Exception as e:
        logging.error(f"Error deleting pet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the pet",
        ) 
