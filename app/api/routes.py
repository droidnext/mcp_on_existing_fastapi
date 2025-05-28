from fastapi import APIRouter, Request
from app.mcp.mcp_routes import mcp_app
from app.api.movie_routes import router as movie_router

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Main app running. FastMCP available at /mcp/docs"}

@router.get("/whoami")
async def whoami(request: Request):
    return {"user": request.state.user}

# Include movie routes
router.include_router(movie_router) 