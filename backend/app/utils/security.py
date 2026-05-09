"""Security utilities for preventing dangerous operations."""

import re
from typing import List
from app.utils.logger import logger


# Dangerous command patterns that should be blocked
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",  # rm -rf /
    r"dd\s+if=|dd\s+of=",  # dd operations
    r"mkfs",  # Format filesystem
    r":\(\)|:(){",  # Fork bomb
    r">\s*/dev/sda|>\s*/dev/hda",  # Write to disk
]

# Commands that require confirmation
CONFIRMATION_REQUIRED = [
    r"rm\s+-rf",  # rm -rf
    r"git\s+reset\s+--hard",  # git reset
    r"git\s+clean",  # git clean
    r"rm\s+",  # rm without -rf
]


def is_command_dangerous(command: str) -> bool:
    """
    Check if a command contains dangerous patterns.
    
    Args:
        command: Command to check
        
    Returns:
        True if command is dangerous
    """
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            logger.warning(f"Dangerous command blocked: {command}")
            return True
    return False


def requires_confirmation(command: str) -> bool:
    """
    Check if a command requires user confirmation.
    
    Args:
        command: Command to check
        
    Returns:
        True if command needs confirmation
    """
    for pattern in CONFIRMATION_REQUIRED:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def sanitize_shell_command(command: str) -> str:
    """
    Sanitize shell command by removing potentially dangerous characters.
    
    Args:
        command: Command to sanitize
        
    Returns:
        Sanitized command
    """
    # Remove double ampersand chaining dangerous commands
    dangerous_chains = [
        (r";rm\s+", ";"),  # Remove chained rm
        (r";dd\s+", ";"),  # Remove chained dd
    ]
    
    sanitized = command
    for pattern, replacement in dangerous_chains:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    return sanitized


def validate_file_path(path: str, allowed_extensions: List[str] = None) -> bool:
    """
    Validate file path for safety and allowed extensions.
    
    Args:
        path: File path to validate
        allowed_extensions: List of allowed extensions (e.g., ['.py', '.js'])
        
    Returns:
        True if path is valid
    """
    # Check for null bytes
    if '\x00' in path:
        logger.warning(f"Null byte detected in path: {path}")
        return False
    
    # Check for path traversal
    if ".." in path or path.startswith("/"):
        logger.warning(f"Path traversal attempt: {path}")
        return False
    
    # Check extensions if specified
    if allowed_extensions:
        if not any(path.endswith(ext) for ext in allowed_extensions):
            logger.warning(f"File extension not allowed: {path}")
            return False
    
    return True
