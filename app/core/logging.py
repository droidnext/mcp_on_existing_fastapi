"""
Logging configuration for the application.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(env: str = "dev", log_level: str = None):
    """
    Setup application logging with environment-specific configuration.
    
    Args:
        env: Application environment ('dev' or 'prod')
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Determine log level
    if log_level:
        level = getattr(logging, log_level.upper(), logging.INFO)
    elif env == "prod":
        level = logging.INFO
    else:
        level = logging.DEBUG

    # Log format
    if env == "prod":
        # Structured logging for production (JSON-like format)
        log_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "%(funcName)s:%(lineno)d | %(message)s"
        )
    else:
        # Human-readable format for development
        log_format = "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format))

    root_logger.addHandler(console_handler)

    # File handler for production (optional)
    if env == "prod":
        log_dir = os.getenv("LOG_DIR", "/var/log/app")
        try:
            os.makedirs(log_dir, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                filename=os.path.join(log_dir, "app.log"),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter(log_format))
            root_logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            # If we can't write to log directory, continue without file logging
            logging.warning(f"Could not create file handler: {e}")

    # Set log levels for third-party libraries (suppress verbose logs)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Suppress FastMCP internal task queue logs (docket, fakeredis)
    logging.getLogger("docket").setLevel(logging.WARNING)
    logging.getLogger("docket.worker").setLevel(logging.WARNING)
    logging.getLogger("fakeredis").setLevel(logging.WARNING)
    
    # Suppress other noisy third-party libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logging.info(f"Logging configured for environment: {env} (level: {logging.getLevelName(level)})") 