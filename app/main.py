from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.api.routes import auth, users, profiles, pets, bookings, sitters

app = FastAPI(
    title="Waggy API",
    description="API for the Waggy Sitters pet sitting application",
    version="1.0.0",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Events
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"],
)
app.include_router(
    users.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["Users"],
)
app.include_router(
    profiles.router,
    prefix=f"{settings.API_V1_PREFIX}/profiles",
    tags=["Profiles"],
)
app.include_router(
    pets.router,
    prefix=f"{settings.API_V1_PREFIX}/pets",
    tags=["Pets"],
)
app.include_router(
    bookings.router,
    prefix=f"{settings.API_V1_PREFIX}/bookings",
    tags=["Bookings"],
)
app.include_router(
    sitters.router,
    prefix=f"{settings.API_V1_PREFIX}/sitters",
    tags=["Sitters"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Waggy API",
        "docs": "/docs",
    } 
