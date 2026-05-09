"""Logging configuration for the application."""

from loguru import logger as _logger
import sys
from pathlib import Path

# Create logs directory if it doesn't exist
log_dir = Path("./logs")
log_dir.mkdir(exist_ok=True)

# Remove default handler
_logger.remove()

# Add console handler
_logger.add(
    sys.stdout,
    format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
)

# Add file handler
_logger.add(
    log_dir / "app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="500 MB",
    retention="7 days",
)

# Export logger instance
logger = _logger
