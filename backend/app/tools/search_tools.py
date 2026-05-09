"""File search and grep tools."""

import re
from typing import Optional, List
from pathlib import Path

from app.config import settings
from app.utils.logger import logger
from app.utils.path_utils import get_safe_path, is_within_workspace
from app.models.file_models import SearchResult, SearchResponse


async def search_files(
    pattern: str,
    path: Optional[str] = None,
    is_regex: bool = False,
    case_sensitive: bool = False
) -> Optional[SearchResponse]:
    """
    Search for pattern in files.
    
    Args:
        pattern: Search pattern (text or regex)
        path: Search within directory (relative to workspace)
        is_regex: Use regex pattern
        case_sensitive: Case sensitive search
        
    Returns:
        SearchResponse with results
    """
    try:
        # Determine search directory
        if path:
            search_dir = get_safe_path(path)
        else:
            search_dir = settings.workspace_dir
        
        if not search_dir or not search_dir.is_dir():
            logger.error(f"Invalid search directory: {path}")
            return None
        
        results: List[SearchResult] = []
        
        # Compile regex if needed
        if is_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                compiled_pattern = re.compile(pattern, flags)
            except re.error as e:
                logger.error(f"Invalid regex pattern: {e}")
                return None
        
        # Search through files
        for file_path in search_dir.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Skip binary files
            if _is_binary_file(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        match = False
                        
                        if is_regex:
                            match = compiled_pattern.search(line)
                        else:
                            if case_sensitive:
                                match = pattern in line
                            else:
                                match = pattern.lower() in line.lower()
                        
                        if match:
                            relative_path = file_path.relative_to(settings.workspace_dir)
                            results.append(SearchResult(
                                file_path=str(relative_path),
                                line_number=line_num,
                                content=line.rstrip()
                            ))
            
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")
        
        logger.info(f"Search found {len(results)} matches for pattern: {pattern}")
        
        return SearchResponse(
            pattern=pattern,
            results=results,
            total_matches=len(results)
        )
    
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        return None


def _is_binary_file(file_path: Path) -> bool:
    """
    Check if a file is binary.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if file appears to be binary
    """
    binary_extensions = {
        '.pyc', '.pyo', '.so', '.o', '.a',
        '.exe', '.dll', '.lib', '.jar', '.zip',
        '.png', '.jpg', '.jpeg', '.gif', '.ico',
        '.mp3', '.mp4', '.avi', '.mov',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx'
    }
    
    if file_path.suffix.lower() in binary_extensions:
        return True
    
    # Check file content for null bytes
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(512)
            return b'\x00' in chunk
    except Exception:
        return True


async def search_in_file(
    file_path: str,
    pattern: str,
    is_regex: bool = False
) -> Optional[SearchResponse]:
    """
    Search for pattern in a specific file.
    
    Args:
        file_path: File path relative to workspace
        pattern: Search pattern
        is_regex: Use regex pattern
        
    Returns:
        SearchResponse with results
    """
    try:
        safe_path = get_safe_path(file_path)
        if not safe_path or not safe_path.is_file():
            logger.error(f"File not found: {file_path}")
            return None
        
        results: List[SearchResult] = []
        
        # Compile regex if needed
        if is_regex:
            try:
                compiled_pattern = re.compile(pattern)
            except re.error as e:
                logger.error(f"Invalid regex: {e}")
                return None
        
        with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                match = False
                
                if is_regex:
                    match = compiled_pattern.search(line)
                else:
                    match = pattern in line
                
                if match:
                    results.append(SearchResult(
                        file_path=file_path,
                        line_number=line_num,
                        content=line.rstrip()
                    ))
        
        return SearchResponse(
            pattern=pattern,
            results=results,
            total_matches=len(results)
        )
    
    except Exception as e:
        logger.error(f"Error searching in file: {e}")
        return None


async def get_line_context(
    file_path: str,
    line_number: int,
    context_lines: int = 3
) -> Optional[dict]:
    """
    Get context around a specific line.
    
    Args:
        file_path: File path relative to workspace
        line_number: Line number (1-based)
        context_lines: Number of context lines before/after
        
    Returns:
        Dict with context or None
    """
    try:
        safe_path = get_safe_path(file_path)
        if not safe_path or not safe_path.is_file():
            return None
        
        with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        context = {
            "file_path": file_path,
            "line_number": line_number,
            "context": [
                {
                    "line_num": i + 1,
                    "content": lines[i].rstrip(),
                    "is_target": i + 1 == line_number
                }
                for i in range(start, end)
            ]
        }
        
        return context
    
    except Exception as e:
        logger.error(f"Error getting line context: {e}")
        return None
