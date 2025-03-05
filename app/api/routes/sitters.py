"""Sitter routes."""
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(
    prefix="/sitters",
    tags=["sitters"],
)


@router.get("/")
async def get_sitters():
    """Get all available sitters."""
    # For now, just return mock sitters
    return [
        {
            "id": "sitter1",
            "user_id": "user1",
            "first_name": "Jane",
            "last_name": "Smith",
            "profile_image": "https://example.com/profile1.jpg",
            "bio": "Professional pet sitter with 5 years experience",
            "services": ["dog walking", "overnight care"],
            "rate": 25.0,
            "rating": 4.8,
            "reviews_count": 15,
        },
        {
            "id": "sitter2",
            "user_id": "user2",
            "first_name": "Mike",
            "last_name": "Johnson",
            "profile_image": "https://example.com/profile2.jpg",
            "bio": "Animal lover with veterinary assistant experience",
            "services": ["dog walking", "pet sitting", "medication administration"],
            "rate": 30.0,
            "rating": 4.9,
            "reviews_count": 27,
        },
    ]


@router.get("/search")
async def search_sitters():
    """Search for sitters with filters (location, service, availability, etc.)."""
    # For now, just return same mock sitters
    return [
        {
            "id": "sitter1",
            "user_id": "user1",
            "first_name": "Jane",
            "last_name": "Smith",
            "profile_image": "https://example.com/profile1.jpg",
            "bio": "Professional pet sitter with 5 years experience",
            "services": ["dog walking", "overnight care"],
            "rate": 25.0,
            "rating": 4.8,
            "reviews_count": 15,
        },
    ]


@router.get("/{sitter_id}")
async def get_sitter(sitter_id: str):
    """Get a specific sitter by ID."""
    return {
        "id": sitter_id,
        "user_id": "user1",
        "first_name": "Jane",
        "last_name": "Smith",
        "profile_image": "https://example.com/profile1.jpg",
        "bio": "Professional pet sitter with 5 years experience",
        "services": ["dog walking", "overnight care"],
        "rate": 25.0,
        "rating": 4.8,
        "reviews_count": 15,
        "availability": [
            {"day": "Monday", "start": "9:00", "end": "17:00"},
            {"day": "Tuesday", "start": "9:00", "end": "17:00"},
            {"day": "Wednesday", "start": "9:00", "end": "17:00"},
            {"day": "Thursday", "start": "9:00", "end": "17:00"},
            {"day": "Friday", "start": "9:00", "end": "17:00"},
        ],
    }


@router.get("/{sitter_id}/reviews")
async def get_sitter_reviews(sitter_id: str):
    """Get reviews for a specific sitter."""
    return [
        {
            "id": "review1",
            "sitter_id": sitter_id,
            "owner_id": "owner1",
            "rating": 5,
            "comment": "Jane was amazing with my dog Buddy!",
            "created_at": "2024-01-15T14:30:00",
        },
        {
            "id": "review2",
            "sitter_id": sitter_id,
            "owner_id": "owner2",
            "rating": 4.5,
            "comment": "Very professional and caring.",
            "created_at": "2024-02-22T10:15:00",
        },
    ]


@router.post("/{sitter_id}/reviews")
async def create_review(sitter_id: str):
    """Create a review for a sitter."""
    return {"message": "Review created successfully", "review_id": "new_review_id"} 
