#!/usr/bin/env python
"""Run script for AI Workspace backend server."""

import sys
import os
import uvicorn
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.utils.logger import logger


def main():
    """Run the FastAPI server."""
    logger.info(f"Starting {settings.APP_NAME} server...")
    logger.info(f"Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"Debug: {settings.DEBUG}")
    logger.info(f"Workspace: {settings.workspace_dir}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
