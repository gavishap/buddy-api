from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from app.api.deps import get_current_user, get_current_active_user
from app.schemas.review import Review, ReviewCreate, ReviewUpdate, ReviewWithDetails
from app.db.mongodb import get_database
import logging

router = APIRouter()

@router.post("/", response_model=Review)
async def create_review(
    review_in: ReviewCreate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Create a new review.
    """
    db = await get_database()
    
    # Ensure owner_id matches current user
    if review_in.owner_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner ID must match current user ID",
        )
    
    # Verify booking exists and belongs to the owner
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(review_in.booking_id)})
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )
        
        if booking["owner_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Booking does not belong to you",
            )
        
        if booking["status"] != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only review completed bookings",
            )
        
        # Verify sitter ID matches booking sitter
        if review_in.sitter_id != booking["sitter_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sitter ID must match booking sitter ID",
            )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid booking ID format",
        )
    
    # Check if review already exists for this booking
    existing_review = await db.reviews.find_one({"booking_id": review_in.booking_id})
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review already exists for this booking",
        )
    
    # Prepare review data
    review_data = review_in.dict()
    review_data["created_at"] = None  # Will be set to current time by MongoDB
    
    try:
        # Insert review
        result = await db.reviews.insert_one(review_data)
        review_id = result.inserted_id
        
        # Update sitter's rating
        sitter = await db.profiles.find_one({"user_id": review_in.sitter_id})
        if sitter:
            current_rating = sitter.get("rating", 0)
            current_count = sitter.get("rating_count", 0)
            
            # Calculate new rating
            new_count = current_count + 1
            new_rating = ((current_rating * current_count) + review_in.rating) / new_count
            
            # Update sitter profile
            await db.profiles.update_one(
                {"user_id": review_in.sitter_id},
                {"$set": {
                    "rating": round(new_rating, 1),
                    "rating_count": new_count,
                    "updated_at": None
                }}
            )
        
        # Get created review
        created_review = await db.reviews.find_one({"_id": review_id})
        created_review["id"] = str(created_review.pop("_id"))
        
        return created_review
        
    except Exception as e:
        logging.error(f"Error creating review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the review",
        )

@router.get("/", response_model=List[Review])
async def read_reviews(
    skip: int = 0,
    limit: int = 100,
    sitter_id: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve reviews.
    """
    db = await get_database()
    
    # Build query
    query = {}
    
    if sitter_id:
        query["sitter_id"] = sitter_id
    
    # Execute query
    reviews = await db.reviews.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    # Convert _id to id for each review
    for review in reviews:
        review["id"] = str(review.pop("_id"))
    
    return reviews

@router.get("/{review_id}", response_model=ReviewWithDetails)
async def read_review(
    review_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific review by id with detailed information.
    """
    db = await get_database()
    
    try:
        review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid review ID format",
        )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    
    # Convert _id to id
    review["id"] = str(review.pop("_id"))
    
    # Get owner details
    owner = await db.profiles.find_one({"user_id": review["owner_id"]})
    if owner:
        owner["id"] = str(owner.pop("_id"))
        review["owner"] = owner
    else:
        review["owner"] = {"user_id": review["owner_id"]}
    
    # Get sitter details
    sitter = await db.profiles.find_one({"user_id": review["sitter_id"]})
    if sitter:
        sitter["id"] = str(sitter.pop("_id"))
        review["sitter"] = sitter
    else:
        review["sitter"] = {"user_id": review["sitter_id"]}
    
    # Get booking details
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(review["booking_id"])})
        if booking:
            booking["id"] = str(booking.pop("_id"))
            review["booking"] = booking
        else:
            review["booking"] = {"id": review["booking_id"]}
    except Exception:
        review["booking"] = {"id": review["booking_id"]}
    
    return review

@router.put("/{review_id}", response_model=Review)
async def update_review(
    review_id: str,
    review_in: ReviewUpdate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Update a review.
    """
    db = await get_database()
    
    try:
        review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid review ID format",
        )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    
    # Check if current user is the owner
    if review["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Prepare update data
    update_data = review_in.dict(exclude_unset=True)
    update_data["updated_at"] = None  # Will be set to current time by MongoDB
    
    try:
        # Update review
        await db.reviews.update_one(
            {"_id": ObjectId(review_id)},
            {"$set": update_data}
        )
        
        # If rating changed, update sitter's rating
        if "rating" in update_data:
            old_rating = review["rating"]
            new_rating = update_data["rating"]
            
            if old_rating != new_rating:
                sitter = await db.profiles.find_one({"user_id": review["sitter_id"]})
                if sitter:
                    current_rating = sitter.get("rating", 0)
                    current_count = sitter.get("rating_count", 0)
                    
                    if current_count > 0:
                        # Calculate new rating
                        total_rating = current_rating * current_count
                        total_rating = total_rating - old_rating + new_rating
                        updated_rating = total_rating / current_count
                        
                        # Update sitter profile
                        await db.profiles.update_one(
                            {"user_id": review["sitter_id"]},
                            {"$set": {
                                "rating": round(updated_rating, 1),
                                "updated_at": None
                            }}
                        )
        
        # Get updated review
        updated_review = await db.reviews.find_one({"_id": ObjectId(review_id)})
        updated_review["id"] = str(updated_review.pop("_id"))
        
        return updated_review
        
    except Exception as e:
        logging.error(f"Error updating review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the review",
        )

@router.delete("/{review_id}", response_model=Review)
async def delete_review(
    review_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Delete a review.
    """
    db = await get_database()
    
    try:
        review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid review ID format",
        )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    
    # Check if current user is the owner
    if review["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    try:
        # Delete review
        result = await db.reviews.delete_one({"_id": ObjectId(review_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )
        
        # Update sitter's rating
        sitter = await db.profiles.find_one({"user_id": review["sitter_id"]})
        if sitter:
            current_rating = sitter.get("rating", 0)
            current_count = sitter.get("rating_count", 0)
            
            if current_count > 1:
                # Calculate new rating
                total_rating = current_rating * current_count
                total_rating = total_rating - review["rating"]
                updated_rating = total_rating / (current_count - 1)
                
                # Update sitter profile
                await db.profiles.update_one(
                    {"user_id": review["sitter_id"]},
                    {"$set": {
                        "rating": round(updated_rating, 1),
                        "rating_count": current_count - 1,
                        "updated_at": None
                    }}
                )
            elif current_count == 1:
                # If this was the only review, reset rating
                await db.profiles.update_one(
                    {"user_id": review["sitter_id"]},
                    {"$set": {
                        "rating": None,
                        "rating_count": 0,
                        "updated_at": None
                    }}
                )
        
        # Convert _id to id for response
        review["id"] = str(review.pop("_id"))
        
        return review
        
    except Exception as e:
        logging.error(f"Error deleting review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the review",
        ) 
