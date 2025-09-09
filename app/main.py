import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import LoggingMiddleware, JWTAuthMiddleware, OriginValidationMiddleware
from app.core.lifespan import shared_lifespan
from app.api.routes import router as api_router
from app.mcp.mcp_routes import mcp_app

# Conditionally import elicitation routes based on environment variable
if os.getenv("ENABLE_ELICITATION", "false").lower() == "true":
    from app.mcp.mcp_elicitation_routes import mcp_elicitation
else:
    mcp_elicitation = None

logger = logging.getLogger("MainApp")

# Create main FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    # lifespan=shared_lifespan
    lifespan=mcp_app.lifespan
)

# Apply middleware
app.add_middleware(LoggingMiddleware)

# Conditionally apply JWT middleware
logger.info(f"ENABLE_JWT: {settings.ENABLE_JWT}")
if settings.ENABLE_JWT:
    app.add_middleware(JWTAuthMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add origin validation middleware
app.add_middleware(OriginValidationMiddleware)

# Include API routes
app.include_router(api_router)


# Mount FastMCP app Endpoints /mcp-server/mcp
app.mount("/", mcp_app)

# Conditionally mount FastMCP elicitation app based on environment variable
if settings.ENABLE_ELICITATION and mcp_elicitation is not None:
    logger.info("Elicitation mode enabled - mounting elicitation endpoints")
    app.mount("/mcp-server/elicitation", mcp_elicitation.http_app(path="/mcp-server/elicitation", transport='streamable-http'))
else:
    logger.info("Elicitation mode disabled - skipping elicitation endpoints")

@app.get("/routes")
async def list_routes(request: Request):
    """List all available routes in the application"""
    routes = []
    for route in request.app.routes:
        route_info = {
            "path": route.path,
            "name": route.name,
            "methods": route.methods if hasattr(route, "methods") else ["*"],
            "endpoint": route.endpoint.__name__ if hasattr(route, "endpoint") else str(route),
        }
        routes.append(route_info)
    return {"routes": routes}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 