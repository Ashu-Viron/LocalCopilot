"""Dependency injection setup for FastAPI."""

from typing import Generator
from app.config import settings


async def get_settings() -> dict:
    """
    Dependency to provide settings to route handlers.
    
    Returns:
        dict: Settings object
    """
    return settings
