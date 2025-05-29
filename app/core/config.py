from pydantic_settings import BaseSettings
from typing import List
import yaml
import os
from pathlib import Path

def load_yaml_config():
    """Load configuration from YAML file based on environment"""
    # Get environment from environment variable, default to 'dev'
    env = os.getenv("APP_ENV", "dev")
    
    # Construct config file path
    config_path = Path(__file__).parent.parent.parent / "config" / f"app_config.{env}.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Load YAML configuration
yaml_config = load_yaml_config()

class Settings(BaseSettings):
    # Environment
    ENV: str = os.getenv("APP_ENV", "dev")
    
    # Project settings
    PROJECT_NAME: str = yaml_config["project"]["name"]
    VERSION: str = yaml_config["project"]["version"]
    API_V1_STR: str = yaml_config["project"]["api_v1_str"]
    
    # Server settings
    ALLOWED_HOSTS: List[str] = yaml_config["server"]["allowed_hosts"]
    
    # MCP settings
    MCP_TOOL_TIMEOUT: int = yaml_config["mcp"]["tool_timeout"]

    # Auth settings
    ENABLE_JWT: bool = yaml_config["auth"]["enable_jwt"]
    JWT_SECRET_KEY: str = yaml_config["auth"]["secret_key"]
    JWT_ALGORITHM: str = yaml_config["auth"]["algorithm"]

    class Config:
        case_sensitive = True
        env_file = ".env"  # Allow overriding settings via .env file

settings = Settings() 