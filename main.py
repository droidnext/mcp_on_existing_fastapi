# from fastapi import FastAPI
# from app.core.config import settings
# from app.core.middleware import LoggingMiddleware, JWTAuthMiddleware
# from app.core.lifespan import shared_lifespan
# from app.api.routes import router as api_router
# from app.mcp.mco_routes import mcp_app
# from phoenix.otel import register


# # Connect to your Phoenix instance
# tracer_provider = register(auto_instrument=True)

# # Create main FastAPI app
# app = FastAPI(
#     title=settings.PROJECT_NAME,
#     version=settings.VERSION,
#     lifespan=shared_lifespan
# )


# # Include API routes
# app.include_router(api_router)

# # Mount FastMCP app
# app.mount("/mcp", mcp_app)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
