"""Main FastAPI application."""
import logging

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.api.routes import auth, users, profiles, pets, bookings, sitters

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AuthHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware to extract authorization token from header."""
    
    async def dispatch(self, request: Request, call_next):
        """Extract authorization header and add to request state."""
        authorization = request.headers.get("Authorization")
        request.state.authorization = authorization
        response = await call_next(request)
        return response


def get_authorization(request: Request):
    """Get authorization from request state."""
    return request.state.authorization


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    debug=settings.DEBUG,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add auth header middleware
app.add_middleware(AuthHeaderMiddleware)

# MongoDB startup and shutdown
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Include API routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR, dependencies=[Depends(get_authorization)])
app.include_router(profiles.router, prefix=settings.API_V1_STR)
app.include_router(pets.router, prefix=settings.API_V1_STR)
app.include_router(bookings.router, prefix=settings.API_V1_STR)
app.include_router(sitters.router, prefix=settings.API_V1_STR)

# Add direct token endpoint for OAuth2
@app.post(f"{settings.API_V1_STR}/token")
async def token_endpoint(form_data=Depends(auth.login)):
    """OAuth2 compatible token endpoint."""
    return await auth.login(form_data)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Waggy API"}

@app.get(f"{settings.API_V1_STR}")
async def api_root():
    """API root endpoint."""
    return {"message": "Waggy API v1"}
