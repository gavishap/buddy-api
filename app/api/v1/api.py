from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, profiles, pets, bookings, reviews, messages, availability

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(pets.router, prefix="/pets", tags=["pets"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(availability.router, prefix="/availability", tags=["availability"]) 
