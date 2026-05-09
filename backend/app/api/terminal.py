"""Terminal API endpoints for real command execution."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.tools.shell_tools import run_command
from app.config import settings
from app.utils.logger import logger

router = APIRouter(prefix="/api/terminal", tags=["terminal"])

# In-memory store for command history (keep up to 100 entries)
_command_history = []

class CommandRequest(BaseModel):
    """Command execution request."""
    command: str
    cwd: Optional[str] = None
    timeout: int = 30


class CommandResponse(BaseModel):
    """Command execution response."""
    command: str
    stdout: str
    stderr: str
    return_code: int
    duration: float
    success: bool


@router.post("/execute", response_model=CommandResponse)
async def execute_command(request: CommandRequest) -> CommandResponse:
    """
    Execute a shell command in the workspace.
    
    Args:
        request: Command request with command string
        
    Returns:
        CommandResponse with stdout, stderr, and return code
    """
    try:
        logger.info(f"Terminal executing: {request.command}")
        
        # Default to workspace directory if no cwd specified
        workspace_root = str(settings.workspace_dir)
        
        result = await run_command(
            command=request.command,
            cwd=request.cwd or workspace_root,
            timeout=request.timeout,
            require_confirmation=False  # Frontend already confirmed
        )
        
        if result is None:
            return CommandResponse(
                command=request.command,
                stdout="",
                stderr="Command execution failed or timed out",
                return_code=-1,
                duration=0,
                success=False
            )
        
        response = CommandResponse(
            command=result.command,
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.return_code,
            duration=result.duration,
            success=result.return_code == 0
        )
        
        # Save to history
        _command_history.append({
            "command": response.command,
            "success": response.success,
            "duration": response.duration,
            "cwd": request.cwd or workspace_root
        })
        if len(_command_history) > 100:
            _command_history.pop(0)
            
        return response
        
    except Exception as e:
        logger.error(f"Terminal execute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history() -> dict:
    """Get command history (newest first)."""
    return {"history": list(reversed(_command_history))}
