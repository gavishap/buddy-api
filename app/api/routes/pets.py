"""Pet routes."""
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(
    prefix="/pets",
    tags=["pets"],
)


@router.get("/")
async def get_pets():
    """Get all pets for the current owner."""
    # For now, just return mock pets
    return [
        {
            "id": "pet1",
            "owner_id": "mock_user_id",
            "name": "Buddy",
            "type": "Dog",
            "breed": "Golden Retriever",
            "age": 3,
            "weight": 70.5,
            "special_needs": "None",
        },
        {
            "id": "pet2",
            "owner_id": "mock_user_id",
            "name": "Whiskers",
            "type": "Cat",
            "breed": "Tabby",
            "age": 5,
            "weight": 12.2,
            "special_needs": "Medication twice daily",
        },
    ]


@router.post("/")
async def create_pet():
    """Create a new pet profile."""
    return {"message": "Pet created successfully", "pet_id": "new_pet_id"}


@router.get("/{pet_id}")
async def get_pet(pet_id: str):
    """Get a specific pet by ID."""
    return {
        "id": pet_id,
        "owner_id": "mock_user_id",
        "name": "Buddy",
        "type": "Dog",
        "breed": "Golden Retriever",
        "age": 3,
        "weight": 70.5,
        "special_needs": "None",
    }


@router.put("/{pet_id}")
async def update_pet(pet_id: str):
    """Update a pet profile."""
    return {"message": f"Pet {pet_id} updated successfully"}


@router.delete("/{pet_id}")
async def delete_pet(pet_id: str):
    """Delete a pet profile."""
    return {"message": f"Pet {pet_id} deleted successfully"} 
