import logging
import os
from pathlib import Path
from typing import List

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def load_yaml_config():
    """Load configuration from YAML file based on environment."""
    # Get environment from environment variable, default to 'dev'
    env = os.getenv("APP_ENV", "dev")

    # Construct config file path
    config_path = Path(__file__).parent.parent.parent / "config" / f"app_config.{env}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config file {config_path}: {e}")
        raise


# Load YAML configuration
try:
    yaml_config = load_yaml_config()
except Exception as e:
    logger.warning(f"Failed to load YAML config, using defaults: {e}")
    yaml_config = {}


class Settings(BaseSettings):
    """Application settings with validation and environment variable support."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    ENV: str = Field(default="dev", description="Application environment (dev, prod)")

    # Project settings
    PROJECT_NAME: str = Field(
        default=yaml_config.get("project", {}).get("name", "FastAPI MCP Application"),
        description="Project name",
    )
    VERSION: str = Field(
        default=yaml_config.get("project", {}).get("version", "1.0.0"),
        description="Application version",
    )
    API_V1_STR: str = Field(
        default=yaml_config.get("project", {}).get("api_v1_str", "/api/v1"),
        description="API v1 prefix",
    )

    # Server settings
    ALLOWED_HOSTS: List[str] = Field(
        default_factory=lambda: yaml_config.get("server", {}).get("allowed_hosts", ["*"]),
        description="Allowed CORS origins",
    )

    # MCP settings
    MCP_TOOL_TIMEOUT: int = Field(
        default=yaml_config.get("mcp", {}).get("tool_timeout", 60),
        ge=1,
        le=300,
        description="MCP tool timeout in seconds",
    )
    MCP_TRANSPORT: str = Field(
        default=yaml_config.get("mcp", {}).get("transport", "streamable-http"),
        pattern="^(streamable-http|stdio)$",
        description="MCP transport type: 'streamable-http' (HTTP-based) or 'stdio' (standard I/O)",
    )
    ENABLE_ELICITATION: bool = Field(
        default=os.getenv("ENABLE_ELICITATION", "false").lower() == "true",
        description="Enable MCP elicitation features",
    )

    # Auth settings
    ENABLE_JWT: bool = Field(
        default=yaml_config.get("auth", {}).get("enable_jwt", False),
        description="Enable JWT authentication",
    )
    JWT_SECRET_KEY: str = Field(
        default=os.getenv("JWT_SECRET_KEY", yaml_config.get("auth", {}).get("secret_key", "")),
        description="JWT secret key (optional if using JWKS via 'jku' header, required for symmetric algorithms like HS256)",
    )
    JWT_ALGORITHM: str = Field(
        default=yaml_config.get("auth", {}).get("algorithm", "HS256"),
        pattern="^(HS256|HS384|HS512|RS256|RS384|RS512|ES256|ES384|ES512)$",
        description="Default JWT signing algorithm (used if not specified in token header)",
    )
    JWT_ALLOWED_ALGORITHMS: List[str] = Field(
        default_factory=lambda: yaml_config.get("auth", {}).get(
            "allowed_algorithms",
            ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
        ),
        description="List of allowed JWT algorithms (validates token header 'alg' against this list)",
    )

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """
        Validate JWT secret key strength.
        
        Note: secret_key is only required for symmetric algorithms (HS256/HS384/HS512).
        For asymmetric algorithms with JWKS (RS256/ES256), tokens can use 'jku' header
        to fetch public keys, so secret_key may be empty (defaults to JWKS).
        
        If JWT_SECRET_KEY is empty/not set, the system will default to using JWKS
        (JSON Web Key Set) for token validation via the 'jku' header in tokens.
        """
        enable_jwt = info.data.get("ENABLE_JWT", False)
        env = info.data.get("ENV", "dev")
        
        # Allow empty string - defaults to JWKS when JWT is enabled
        # Empty is always allowed (for JWKS or when JWT is disabled)
        if not v or not v.strip():
            return v
        
        # If JWT is disabled, allow any value (no validation needed)
        if not enable_jwt:
            return v
        
        # Only validate length if JWT is enabled AND a secret key is provided
        # (If empty, we assume JWKS will be used)
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters if provided")
        
        # Stricter requirements for production
        if env == "prod":
            if len(v) < 64:
                raise ValueError("JWT_SECRET_KEY must be at least 64 characters in production")
            
            # Check if using placeholder value
            if "${JWT_SECRET_KEY}" in v or v in ["change-me-in-production", "dev-secret-key"]:
                raise ValueError("JWT_SECRET_KEY must be set to a real value in production")
        
        return v

    @field_validator("ALLOWED_HOSTS")
    @classmethod
    def validate_allowed_hosts(cls, v: List[str], info) -> List[str]:
        """Validate allowed hosts configuration."""
        env = info.data.get("ENV", "dev")
        if env == "prod" and "*" in v:
            logger.warning("ALLOWED_HOSTS contains '*' in production - this is insecure")
        return v

    @field_validator("ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """Validate environment value."""
        if v not in ["dev", "prod"]:
            raise ValueError("ENV must be 'dev' or 'prod'")
        return v


settings = Settings() 