import logging
import os

from app.core.logging import setup_logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.middleware import (
    JWTAuthMiddleware,
    LoggingMiddleware,
    OriginValidationMiddleware,
)
from app.mcp.mcp_routes import mcp_app

# Setup logging based on environment
setup_logging(env=settings.ENV, log_level=os.getenv("LOG_LEVEL"))

# Conditionally import elicitation routes based on environment variable
if os.getenv("ENABLE_ELICITATION", "false").lower() == "true":
    from app.mcp.mcp_elicitation_routes import mcp_elicitation_app
else:
    mcp_elicitation_app = None

logger = logging.getLogger("MainApp")

# Create main FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=mcp_app.lifespan,
    docs_url="/docs" if settings.ENV != "prod" else None,  # Disable docs in production
    redoc_url="/redoc" if settings.ENV != "prod" else None,  # Disable redoc in production
    openapi_url="/openapi.json" if settings.ENV != "prod" else None,  # Disable OpenAPI schema in production
)

# Apply middleware
app.add_middleware(LoggingMiddleware)

# Conditionally apply JWT middleware
logger.info(f"ENABLE_JWT: {settings.ENABLE_JWT}")
if settings.ENABLE_JWT:
    app.add_middleware(JWTAuthMiddleware)

# Add CORS middleware (more restrictive in production)
allowed_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
allowed_headers = [
    "Content-Type",
    "Authorization",
    "X-Request-ID",
    "Accept",
    "Origin",
    "Access-Control-Request-Method",
    "Access-Control-Request-Headers",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=allowed_methods,
    allow_headers=allowed_headers,
    expose_headers=["X-Request-ID"],
    max_age=3600,
)

# Add origin validation middleware
app.add_middleware(OriginValidationMiddleware)

# Include API routes
app.include_router(api_router)

# Mount FastMCP app Endpoints /mcp
app.mount("/", mcp_app)

# Conditionally mount FastMCP elicitation app based on environment variable
if settings.ENABLE_ELICITATION and mcp_elicitation_app is not None:
    logger.info("Elicitation mode enabled - mounting elicitation endpoints")
    app.mount("/mcp/elicitation", mcp_elicitation_app)
else:
    logger.info("Elicitation mode disabled - skipping elicitation endpoints")

@app.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    
    Returns 200 OK if the service is healthy and ready to serve requests.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint for Kubernetes and orchestration.
    
    Returns 200 OK if the service is ready to accept traffic.
    """
    try:
        # Add readiness checks here (e.g., database connectivity, external services)
        return {
            "status": "ready",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "error": str(e) if settings.ENV != "prod" else "Service unavailable"},
        )


@app.get("/routes")
async def list_routes(request: Request):
    """List all available routes in the application."""
    routes = []
    for route in request.app.routes:
        route_info = {
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, "methods") else ["*"],
            "endpoint": route.endpoint.__name__ if hasattr(route, "endpoint") else str(route),
        }
        routes.append(route_info)
    return {"routes": routes}


# Global exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with proper error responses."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    error_detail = exc.errors() if settings.ENV != "prod" else "Invalid request data"
    
    logger.warning(f"Validation error - Request-ID: {request_id} - Errors: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": error_detail,
            "request_id": request_id,
        },
    )


# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with proper error responses."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"Unhandled exception - Request-ID: {request_id} - "
        f"Error: {type(exc).__name__}",
        exc_info=True,
    )
    
    error_message = "Internal server error" if settings.ENV == "prod" else str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": error_message,
            "request_id": request_id,
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 