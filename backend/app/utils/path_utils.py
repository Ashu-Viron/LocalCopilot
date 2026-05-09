"""Path utilities for safe workspace operations."""

import os
from pathlib import Path
from typing import Optional
from app.config import settings
from app.utils.logger import logger


def get_safe_path(relative_path: str) -> Optional[Path]:
    """
    Convert a relative path to an absolute safe path within the workspace.
    Prevents path traversal attacks.
    
    Args:
        relative_path: Path relative to workspace
        
    Returns:
        Safe absolute Path or None if path is outside workspace
    """
    try:
        # Normalize the path
        workspace = settings.workspace_dir.resolve()
        requested_path = (workspace / relative_path).resolve()
        
        # Check if the resolved path is within workspace
        if not str(requested_path).startswith(str(workspace)):
            logger.warning(f"Path traversal attempt detected: {relative_path}")
            return None
        
        return requested_path
    except Exception as e:
        logger.error(f"Error resolving path: {e}")
        return None


def get_relative_path(absolute_path: Path) -> Optional[str]:
    """
    Convert an absolute path to relative path from workspace.
    
    Args:
        absolute_path: Absolute path
        
    Returns:
        Relative path string or None if outside workspace
    """
    try:
        workspace = settings.workspace_dir.resolve()
        abs_path = Path(absolute_path).resolve()
        
        # Check if path is within workspace
        if not str(abs_path).startswith(str(workspace)):
            return None
        
        return str(abs_path.relative_to(workspace))
    except Exception as e:
        logger.error(f"Error getting relative path: {e}")
        return None


def is_safe_path(path: str) -> bool:
    """
    Check if a path is safe (within workspace and doesn't traverse).
    
    Args:
        path: Path to check
        
    Returns:
        True if path is safe
    """
    safe_path = get_safe_path(path)
    return safe_path is not None and safe_path.exists()


def is_within_workspace(path: Path) -> bool:
    """
    Check if a path is within the workspace directory.
    
    Args:
        path: Path to check
        
    Returns:
        True if path is within workspace
    """
    try:
        workspace = settings.workspace_dir.resolve()
        abs_path = Path(path).resolve()
        return str(abs_path).startswith(str(workspace))
    except Exception:
        return False


def ensure_dir_exists(path: Path) -> bool:
    """
    Create directory if it doesn't exist.
    
    Args:
        path: Directory path
        
    Returns:
        True if successful
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory: {e}")
        return False
