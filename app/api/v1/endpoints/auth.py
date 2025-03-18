from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.security import create_access_token
from app.api.deps import authenticate_user, get_current_user
from app.schemas.token import Token
from app.schemas.user import User, UserCreate
from app.db.mongodb import get_database
from app.core.security import get_password_hash
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
import logging

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            subject=str(user["_id"]), expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=User)
async def register_user(user_in: UserCreate) -> Any:
    """
    Register a new user.
    """
    db = await get_database()
    
    # Check if user with this email already exists
    existing_user = await db.users.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    
    # Create new user
    user_data = user_in.dict(exclude={"password"})
    user_data["hashed_password"] = get_password_hash(user_in.password)
    user_data["created_at"] = user_data.get("created_at", None)
    
    try:
        result = await db.users.insert_one(user_data)
        user_id = result.inserted_id
        
        # Create user profile
        profile_data = {
            "user_id": str(user_id),
            "first_name": user_in.first_name,
            "last_name": user_in.last_name,
            "email": user_in.email,
            "user_type": user_in.user_type,
            "created_at": user_data.get("created_at", None)
        }
        
        if user_in.user_type == "sitter":
            # Add sitter-specific fields
            profile_data.update({
                "bio": None,
                "services": [],
                "hourly_rate": None,
                "rating": None,
                "rating_count": 0
            })
        
        await db.profiles.insert_one(profile_data)
        
        # Return the created user
        created_user = await db.users.find_one({"_id": user_id})
        created_user["id"] = str(created_user.pop("_id"))
        return created_user
        
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user",
        )

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: dict = Depends(get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.get("/auth/me", response_model=User)
async def read_users_me_alias(
    current_user: dict = Depends(get_current_user),
) -> Any:
    """
    Alias for /me to support the mobile app. 
    Gets current user.
    """
    return current_user 
