from typing import Any, List, Optional, Dict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId

from app.api.deps import get_current_user, get_current_active_user
from app.schemas.message import Message, MessageCreate, MessageUpdate, MessageWithDetails, ConversationSummary
from app.db.mongodb import get_database
import logging

router = APIRouter()

@router.post("/", response_model=Message)
async def create_message(
    message_in: MessageCreate,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Create a new message.
    """
    db = await get_database()
    
    # Ensure sender_id matches current user
    if message_in.sender_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sender ID must match current user ID",
        )
    
    # Verify receiver exists
    receiver = await db.profiles.find_one({"user_id": message_in.receiver_id})
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver not found",
        )
    
    # If booking_id is provided, verify it exists and involves both users
    if message_in.booking_id:
        try:
            booking = await db.bookings.find_one({"_id": ObjectId(message_in.booking_id)})
            if not booking:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Booking not found",
                )
            
            # Check if both users are involved in the booking
            if (booking["owner_id"] != message_in.sender_id and booking["sitter_id"] != message_in.sender_id) or \
               (booking["owner_id"] != message_in.receiver_id and booking["sitter_id"] != message_in.receiver_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Both users must be involved in the booking",
                )
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid booking ID format",
            )
    
    # Prepare message data
    message_data = message_in.dict()
    message_data["created_at"] = None  # Will be set to current time by MongoDB
    
    try:
        # Insert message
        result = await db.messages.insert_one(message_data)
        message_id = result.inserted_id
        
        # Get created message
        created_message = await db.messages.find_one({"_id": message_id})
        created_message["id"] = str(created_message.pop("_id"))
        
        return created_message
        
    except Exception as e:
        logging.error(f"Error creating message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the message",
        )

@router.get("/", response_model=List[Message])
async def read_messages(
    skip: int = 0,
    limit: int = 100,
    other_user_id: str = Query(..., description="ID of the other user in the conversation"),
    booking_id: Optional[str] = Query(None, description="Filter by booking ID"),
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve messages between current user and another user.
    """
    db = await get_database()
    
    # Build query
    query = {
        "$or": [
            {"sender_id": current_user["id"], "receiver_id": other_user_id},
            {"sender_id": other_user_id, "receiver_id": current_user["id"]}
        ]
    }
    
    if booking_id:
        query["booking_id"] = booking_id
    
    # Execute query
    messages = await db.messages.find(query).sort("created_at", 1).skip(skip).limit(limit).to_list(length=limit)
    
    # Convert _id to id for each message
    for message in messages:
        message["id"] = str(message.pop("_id"))
    
    # Mark messages as read if current user is the receiver
    unread_message_ids = [
        ObjectId(message["id"]) 
        for message in messages 
        if message["receiver_id"] == current_user["id"] and not message["is_read"]
    ]
    
    if unread_message_ids:
        await db.messages.update_many(
            {"_id": {"$in": unread_message_ids}},
            {"$set": {"is_read": True, "updated_at": None}}
        )
    
    return messages

@router.get("/conversations", response_model=List[ConversationSummary])
async def read_conversations(
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Get a summary of all conversations for the current user.
    """
    db = await get_database()
    
    # Get all users the current user has exchanged messages with
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"sender_id": current_user["id"]},
                    {"receiver_id": current_user["id"]}
                ]
            }
        },
        {
            "$sort": {"created_at": -1}
        },
        {
            "$group": {
                "_id": {
                    "$cond": [
                        {"$eq": ["$sender_id", current_user["id"]]},
                        "$receiver_id",
                        "$sender_id"
                    ]
                },
                "last_message": {"$first": "$$ROOT"},
                "unread_count": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$eq": ["$receiver_id", current_user["id"]]},
                                {"$eq": ["$is_read", False]}
                            ]},
                            1,
                            0
                        ]
                    }
                },
                "last_updated": {"$first": "$created_at"}
            }
        }
    ]
    
    conversation_summaries = await db.messages.aggregate(pipeline).to_list(length=100)
    
    # Format the response
    result = []
    for summary in conversation_summaries:
        other_user_id = summary["_id"]
        
        # Get other user details
        other_user = await db.profiles.find_one({"user_id": other_user_id})
        if not other_user:
            other_user = {"user_id": other_user_id, "first_name": "Unknown", "last_name": "User"}
        else:
            other_user["id"] = str(other_user.pop("_id"))
        
        # Format last message
        last_message = summary["last_message"]
        last_message["id"] = str(last_message.pop("_id"))
        
        result.append({
            "other_user": other_user,
            "last_message": last_message,
            "unread_count": summary["unread_count"],
            "last_updated": summary["last_updated"]
        })
    
    # Sort by last_updated
    result.sort(key=lambda x: x["last_updated"], reverse=True)
    
    return result

@router.put("/{message_id}/read", response_model=Message)
async def mark_message_as_read(
    message_id: str,
    current_user: dict = Depends(get_current_active_user),
) -> Any:
    """
    Mark a message as read.
    """
    db = await get_database()
    
    try:
        message = await db.messages.find_one({"_id": ObjectId(message_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID format",
        )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    # Check if current user is the receiver
    if message["receiver_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Check if message is already read
    if message["is_read"]:
        # Return the message as is
        message["id"] = str(message.pop("_id"))
        return message
    
    try:
        # Update message
        await db.messages.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"is_read": True, "updated_at": None}}
        )
        
        # Get updated message
        updated_message = await db.messages.find_one({"_id": ObjectId(message_id)})
        updated_message["id"] = str(updated_message.pop("_id"))
        
        return updated_message
        
    except Exception as e:
        logging.error(f"Error updating message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the message",
        ) 
