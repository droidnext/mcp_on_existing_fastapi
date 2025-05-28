from contextlib import asynccontextmanager
import logging

logger = logging.getLogger("App")

@asynccontextmanager
async def shared_lifespan(app):
    logger.info("🚀 Starting up...")
    # Add any startup initialization here
    # e.g., app.state.db = await connect_to_db()
    yield
    logger.info("🛑 Shutting down...")
    # Add any cleanup code here
    # e.g., await app.state.db.close() 