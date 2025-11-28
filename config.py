"""Configuration and environment setup."""
from dotenv import load_dotenv
import os

load_dotenv(override=True)

def get_env(key: str, default: str = None) -> str:
    """Get environment variable with optional default."""
    return os.getenv(key, default)

