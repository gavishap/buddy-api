from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from bson import ObjectId

from app.core.config import settings, collections
from app.core.security import verify_password
from app.db.mongodb import get_database
from app.schemas.token import TokenPayload
from app.schemas.user import UserInDB

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Get the current authenticated user."""
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    db = get_database()
    user = await db[collections.USERS].find_one({"_id": ObjectId(token_data.sub)})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Convert ObjectId to string for serialization
    user["id"] = str(user["_id"])
    del user["_id"]
    
    return UserInDB(**user)

async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user

def get_user_by_email(db, email: str) -> Optional[dict]:
    """Get a user by email."""
    return db[collections.USERS].find_one({"email": email})

async def authenticate_user(db, email: str, password: str) -> Optional[dict]:
    """Authenticate a user."""
    user = await db[collections.USERS].find_one({"email": email})
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    
    # Convert ObjectId to string for serialization
    user["id"] = str(user["_id"])
    del user["_id"]
    
    return user 
