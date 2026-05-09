"""File operation tools."""

import asyncio
import aiofiles
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.config import settings
from app.utils.logger import logger
from app.utils.path_utils import get_safe_path, ensure_dir_exists, is_within_workspace
from app.models.file_models import FileInfo, DirectoryListing, FileReadResponse


async def read_file(path: str, encoding: str = "utf-8") -> Optional[FileReadResponse]:
    """
    Read a file from the workspace.
    
    Args:
        path: Relative file path
        encoding: File encoding
        
    Returns:
        FileReadResponse or None if failed
    """
    try:
        safe_path = get_safe_path(path)
        if not safe_path or not safe_path.exists():
            logger.error(f"File not found: {path}")
            return None
        
        if not safe_path.is_file():
            logger.error(f"Path is not a file: {path}")
            return None
        
        async with aiofiles.open(safe_path, 'r', encoding=encoding) as f:
            content = await f.read()
        
        return FileReadResponse(
            path=path,
            content=content,
            size=safe_path.stat().st_size,
            encoding=encoding,
            lines=len(content.splitlines())
        )
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        return None


async def write_file(path: str, content: str, backup: bool = True) -> Dict[str, Any]:
    """
    Write content to a file in the workspace.
    
    Args:
        path: Relative file path
        content: File content
        backup: Create backup of original file
        
    Returns:
        Dict with success status and details
    """
    try:
        safe_path = get_safe_path(path)
        if not safe_path:
            return {"success": False, "message": "Invalid path"}
        
        # Create backup if requested and file exists
        backup_path = None
        if backup and safe_path.exists():
            backup_path = Path(str(safe_path) + ".bak")
            try:
                import shutil
                shutil.copy2(safe_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            except Exception as e:
                logger.warning(f"Could not create backup: {e}")
        
        # Ensure directory exists
        if not ensure_dir_exists(safe_path):
            return {"success": False, "message": "Cannot create directory"}
        
        # Write file
        original_size = safe_path.stat().st_size if safe_path.exists() else 0
        async with aiofiles.open(safe_path, 'w', encoding='utf-8') as f:
            await f.write(content)
        
        new_size = safe_path.stat().st_size
        
        return {
            "success": True,
            "message": "File written successfully",
            "path": path,
            "size": new_size,
            "backup_path": str(backup_path) if backup_path else None
        }
    except Exception as e:
        logger.error(f"Error writing file {path}: {e}")
        return {"success": False, "message": str(e)}


async def create_file(path: str, content: str = "") -> Dict[str, Any]:
    """
    Create a new file in the workspace.
    
    Args:
        path: Relative file path
        content: Initial content
        
    Returns:
        Dict with success status
    """
    try:
        safe_path = get_safe_path(path)
        if not safe_path:
            return {"success": False, "message": "Invalid path"}
        
        if safe_path.exists():
            return {"success": False, "message": "File already exists"}
        
        if not ensure_dir_exists(safe_path):
            return {"success": False, "message": "Cannot create directory"}
        
        async with aiofiles.open(safe_path, 'w', encoding='utf-8') as f:
            await f.write(content)
        
        logger.info(f"Created file: {path}")
        
        return {
            "success": True,
            "message": "File created",
            "path": path,
            "size": safe_path.stat().st_size
        }
    except Exception as e:
        logger.error(f"Error creating file {path}: {e}")
        return {"success": False, "message": str(e)}


async def delete_file(path: str, backup: bool = False) -> Dict[str, Any]:
    """
    Delete a file from the workspace.
    
    Args:
        path: Relative file path
        backup: Create backup before deleting
        
    Returns:
        Dict with success status
    """
    try:
        safe_path = get_safe_path(path)
        if not safe_path or not safe_path.exists():
            return {"success": False, "message": "File not found"}
        
        if not safe_path.is_file():
            return {"success": False, "message": "Path is not a file"}
        
        # Create backup if requested
        backup_path = None
        if backup:
            backup_path = Path(str(safe_path) + ".deleted")
            try:
                import shutil
                shutil.copy2(safe_path, backup_path)
                logger.info(f"Created backup before deletion: {backup_path}")
            except Exception as e:
                logger.warning(f"Could not create backup: {e}")
        
        safe_path.unlink()
        logger.info(f"Deleted file: {path}")
        
        return {
            "success": True,
            "message": "File deleted",
            "path": path,
            "backup_path": str(backup_path) if backup_path else None
        }
    except Exception as e:
        logger.error(f"Error deleting file {path}: {e}")
        return {"success": False, "message": str(e)}


async def list_directory(path: str = ".") -> Optional[DirectoryListing]:
    """
    List files in a directory.
    
    Args:
        path: Relative directory path
        
    Returns:
        DirectoryListing or None if failed
    """
    try:
        safe_path = get_safe_path(path) or settings.workspace_dir
        
        if not safe_path.exists() or not safe_path.is_dir():
            logger.error(f"Directory not found: {path}")
            return None
        
        files = []
        for item in sorted(safe_path.iterdir()):
            try:
                relative = str(item.relative_to(settings.workspace_dir))
                stat = item.stat()
                
                files.append(FileInfo(
                    path=relative,
                    name=item.name,
                    is_file=item.is_file(),
                    size=stat.st_size if item.is_file() else None,
                    modified_at=datetime.fromtimestamp(stat.st_mtime)
                ))
            except Exception as e:
                logger.warning(f"Error listing item {item}: {e}")
        
        return DirectoryListing(
            path=path,
            files=files,
            total_count=len(files)
        )
    except Exception as e:
        logger.error(f"Error listing directory {path}: {e}")
        return None


async def get_file_info(path: str) -> Optional[FileInfo]:
    """
    Get information about a file.
    
    Args:
        path: Relative file path
        
    Returns:
        FileInfo or None if not found
    """
    try:
        safe_path = get_safe_path(path)
        if not safe_path or not safe_path.exists():
            return None
        
        stat = safe_path.stat()
        relative = str(safe_path.relative_to(settings.workspace_dir))
        
        return FileInfo(
            path=relative,
            name=safe_path.name,
            is_file=safe_path.is_file(),
            size=stat.st_size if safe_path.is_file() else None,
            modified_at=datetime.fromtimestamp(stat.st_mtime)
        )
    except Exception as e:
        logger.error(f"Error getting file info {path}: {e}")
        return None
