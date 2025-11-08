"""API router package."""

from fastapi import APIRouter

api_router = APIRouter(prefix="/api")

# Import and include routers here
# from src.api.hosts import router as hosts_router
# api_router.include_router(hosts_router, tags=["hosts"])
