"""
API routes for the main application.
"""
from fastapi import APIRouter, Request

from app.api.movie_routes import router as movie_router

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint providing basic application information."""
    return {"message": "Main app running. FastMCP available at /mcp/docs"}


@router.get("/whoami")
async def whoami(request: Request):
    """Get current user information from JWT token."""
    return {"user": request.state.user}


# Include movie routes
router.include_router(movie_router) 