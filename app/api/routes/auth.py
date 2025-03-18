"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
from typing import Optional
import logging
from bson import ObjectId
from jose.exceptions import JWTError

from app.core.config import settings, collections
from app.db.mongodb import get_database
from app.models.token import Token
from app.models.user import UserCreate, UserLogin, User
from app.core.security import create_access_token, get_password_hash, verify_password

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/token")

# Define request models
class UserRegister(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

async def get_user_by_email(email: str):
    """Find a user by email in any collection."""
    db = await get_database()
    
    # Try owner collection first
    user = await db[collections.OWNERS].find_one({"email": email})
    if user:
        user["user_type"] = "owner"
        return user
    
    # Try sitter collection
    user = await db[collections.SITTERS].find_one({"email": email})
    if user:
        user["user_type"] = "sitter"
        return user
    
    # Fallback to legacy users collection
    user = await db[collections.USERS].find_one({"email": email})
    return user

async def get_user_by_id(user_id: str):
    """Find a user by ID in any collection."""
    db = await get_database()
    
    # Try each collection
    for collection_name, user_type in [
        (collections.OWNERS, "owner"),
        (collections.SITTERS, "sitter"),
        (collections.USERS, None)  # Legacy
    ]:
        # Try to find by id first
        user = await db[collection_name].find_one({"id": user_id})
        
        # Then try by ObjectId
        if not user:
            try:
                user = await db[collection_name].find_one({"_id": ObjectId(user_id)})
            except Exception:
                pass
        
        if user:
            # Ensure user_type is set
            if user_type and "user_type" not in user:
                user["user_type"] = user_type
            return user, collection_name
    
    return None, None

async def authenticate_user(email: str, password: str):
    """Authenticate user with email and password."""
    db = await get_database()
    logger.info(f"Authenticating user {email} in database {settings.MONGODB_DB_NAME}")
    
    user = await get_user_by_email(email)
    
    if not user:
        logger.warning(f"User not found: {email}")
        return False
    
    # If no hashed_password, try password field
    stored_password = user.get("hashed_password", user.get("password"))
    if not stored_password:
        logger.warning(f"No password found for user: {email}")
        return False
    
    if not verify_password(password, stored_password):
        logger.warning(f"Invalid password for user: {email}")
        return False
    
    # Add id if not exists
    if "id" not in user and "_id" in user:
        user["id"] = str(user["_id"])
    
    logger.info(f"User authenticated successfully: {email}")
    return user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user with email and password."""
    logger.info(f"Login attempt for user: {form_data.username}")
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    user_id = str(user.get("id", user.get("_id", "")))
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Include user_type in token data
    token_data = {
        "sub": user_id,
        "user_type": user.get("user_type", "owner")
    }
    
    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )
    
    logger.info(f"Login successful for user: {form_data.username}, type: {user.get('user_type', 'unknown')}")
    return {"access_token": access_token, "token_type": "bearer"}

# Alternative endpoint for mobile app
@router.post("/token", response_model=Token)
async def login_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user with email and password - alternative endpoint."""
    return await login(form_data)

# Additional alternative endpoints to match the mobile app
@router.post("/auth/login", response_model=Token)
async def login_auth_login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Duplicate login endpoint for compatibility."""
    return await login(form_data)

@router.get("/me")
async def get_current_user(request: Request):
    """Get current user info."""
    # Get the authorization from request state
    authorization = request.state.authorization
    
    if authorization:
        try:
            # Extract token from Authorization header
            if not authorization.startswith("Bearer "):
                logger.warning("Invalid authorization header format")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
            
            token = authorization.replace("Bearer ", "")
            
            # Decode the token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            user_type = payload.get("user_type", "owner")  # Default to owner
            
            if not user_id:
                logger.warning("No user_id in token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="Invalid token"
                )
            
            # Get user from database
            user, collection_name = await get_user_by_id(user_id)
            
            if not user:
                logger.warning(f"User not found: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            
            # Convert _id to string if present
            if "_id" in user:
                user["id"] = str(user["_id"])
                del user["_id"]
            
            # Remove sensitive data
            if "hashed_password" in user:
                del user["hashed_password"]
                
            # Ensure user_type is set
            if "user_type" not in user:
                user["user_type"] = user_type
                
            logger.info(f"User found: {user.get('email')}, type: {user.get('user_type')}")
            return user
                
        except JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        except Exception as e:
            logger.error(f"Error in get_current_user: {str(e)}")
            if settings.ENVIRONMENT != "development":
                raise
    
    # For development, fallback to mock data
    if settings.ENVIRONMENT == "development":
        logger.warning("Returning mock user data as fallback")
        return {
            "id": "mock_user_id",
            "email": "user@example.com",
            "user_type": "owner",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

# Duplicate route to match the pattern the mobile app is using
@router.get("/auth/me")
async def get_current_user_auth_auth(request: Request):
    """Duplicate get current user endpoint for compatibility."""
    return await get_current_user(request)

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user."""
    logger.info(f"Registration attempt for email: {user_data.email}, type: {user_data.user_type}")
    logger.info(f"Using database: {settings.MONGODB_DB_NAME}")
    
    db = await get_database()
    
    # Check if user already exists in any collection
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        logger.warning(f"Email already registered: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user dict
    user_dict = user_data.dict()
    user_dict["hashed_password"] = hashed_password
    del user_dict["password"]  # Remove plain password
    
    # Add created_at timestamp
    user_dict["created_at"] = datetime.utcnow().isoformat()
    user_dict["is_active"] = True
    
    # Determine which collection to use based on user_type
    user_type = user_data.user_type.lower()
    if user_type == "owner":
        collection_name = collections.OWNERS
    elif user_type == "sitter":
        collection_name = collections.SITTERS
    else:
        # Fallback to legacy collection
        collection_name = collections.USERS
    
    # Insert user
    try:
        result = await db[collection_name].insert_one(user_dict)
        user_id = str(result.inserted_id)
        logger.info(f"User registered successfully: {user_data.email}, ID: {user_id}, Collection: {collection_name}")
    except Exception as e:
        logger.error(f"Error inserting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
    
    # Create access token with user_type
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id, "user_type": user_type}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Separate endpoints for owner and sitter registration (for API structure)
@router.post("/register/owner", response_model=Token)
async def register_owner(user_data: UserCreate):
    """Register a new owner."""
    user_data.user_type = "owner"
    return await register(user_data)

@router.post("/register/sitter", response_model=Token)
async def register_sitter(user_data: UserCreate):
    """Register a new sitter."""
    user_data.user_type = "sitter"
    return await register(user_data)

@router.post("/logout")
async def logout():
    """Logout endpoint."""
    return {"message": "Logged out successfully"}
