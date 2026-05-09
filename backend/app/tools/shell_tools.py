"""Shell command execution tools."""

import subprocess
from typing import Optional, Dict, Any
import time

from pydantic import BaseModel

from app.config import settings
from app.utils.logger import logger
from app.utils.security import is_command_dangerous, requires_confirmation


class CommandResult(BaseModel):
    """Result of a shell command execution."""
    command: str
    stdout: str
    stderr: str
    return_code: int
    duration: float


def _run_sync_command(command: str, cwd: Optional[str], timeout: int) -> Optional[CommandResult]:
    """
    Synchronously run a shell command (Windows-friendly).
    
    Args:
        command: Command to execute
        cwd: Working directory (absolute path or None)
        timeout: Timeout in seconds
        
    Returns:
        CommandResult or None if failed
    """
    start = time.time()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            shell=True,           # IMPORTANT for Windows (ls/dir/cd etc.)
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = time.time() - start
        return CommandResult(
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            return_code=completed.returncode,
            duration=duration,
        )
    except subprocess.TimeoutExpired:
        logger.error(f"Command timeout after {timeout}s: {command}")
        return None
    except Exception as e:
        logger.error(f"Error executing command: {e}", exc_info=True)
        return None


async def run_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 30,
    require_confirmation: bool = True
) -> Optional[CommandResult]:
    """
    Execute a shell command in the workspace.
    
    Args:
        command: Command to execute
        cwd: Working directory (absolute path or relative to workspace)
        timeout: Timeout in seconds
        require_confirmation: Whether to check if command needs confirmation
        
    Returns:
        CommandResult or None if failed
    """
    try:
        # Safety checks
        if is_command_dangerous(command):
            logger.error(f"Dangerous command blocked: {command}")
            return None
        
        if require_confirmation and requires_confirmation(command):
            logger.warning(f"Command requires confirmation: {command}")
            pass
        
        # Determine working directory
        if cwd:
            # Check if it's an absolute path or relative
            from pathlib import Path
            cwd_path = Path(cwd)
            if cwd_path.is_absolute():
                work_dir = cwd_path
            else:
                work_dir = settings.workspace_dir / cwd
        else:
            work_dir = settings.workspace_dir
        
        if not work_dir.exists():
            logger.error(f"Working directory does not exist: {work_dir}")
            return None
        
        logger.info(f"Executing command: {command} in {work_dir}")
        
        # Use synchronous subprocess for Windows compatibility
        result = _run_sync_command(command, str(work_dir), timeout)
        
        if result:
            logger.info(f"Command completed with return code {result.return_code}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing command: {e}", exc_info=True)
        return None


async def get_command_info(command: str) -> Dict[str, Any]:
    """
    Get information about whether a command is safe to run.
    
    Args:
        command: Command to check
        
    Returns:
        Dict with safety information
    """
    return {
        "command": command,
        "is_dangerous": is_command_dangerous(command),
        "requires_confirmation": requires_confirmation(command),
        "safe_to_run": not is_command_dangerous(command)
    }
