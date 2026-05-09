"""Tool execution API endpoints."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any
import uuid

from app.models.tool_models import ToolRequest, ToolResult
from app.agent.executor import executor

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.post("/execute", response_model=ToolResult)
async def execute_tool(request: ToolRequest) -> ToolResult:
    """
    Execute a tool.
    
    Args:
        request: ToolRequest with tool type and parameters
        
    Returns:
        ToolResult with execution result
    """
    try:
        result = await executor.execute_tool(
            request.tool,
            request.parameters,
            request.timeout
        )
        if not result:
            raise HTTPException(status_code=500, detail="Tool execution failed")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_execution_logs(limit: Optional[int] = None) -> dict:
    """
    Get tool execution logs.
    
    Args:
        limit: Optional limit on number of logs
        
    Returns:
        List of logs
    """
    try:
        logs = executor.get_logs(limit)
        return {
            "total": len(logs),
            "logs": [log.dict() for log in logs]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logs/clear")
async def clear_execution_logs() -> dict:
    """
    Clear execution logs.
    
    Returns:
        Success message
    """
    try:
        executor.clear_logs()
        return {"message": "Logs cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available")
async def list_available_tools() -> dict:
    """
    List available tools.
    
    Returns:
        Dict with available tools and descriptions
    """
    tools = {
        "file_operations": [
            {"name": "read_file", "description": "Read file contents"},
            {"name": "edit_file", "description": "Modify file content"},
            {"name": "create_file", "description": "Create new files"},
            {"name": "delete_file", "description": "Delete files"},
            {"name": "list_files", "description": "List directory contents"},
            {"name": "search_files", "description": "Search in files"}
        ],
        "shell_operations": [
            {"name": "run_command", "description": "Execute shell commands"}
        ],
        "git_operations": [
            {"name": "git_status", "description": "Get git status"},
            {"name": "git_commit", "description": "Create commit"},
            {"name": "git_diff", "description": "Get git diff"},
            {"name": "git_log", "description": "View git log"},
            {"name": "git_add", "description": "Stage files"},
            {"name": "git_push", "description": "Push changes"},
            {"name": "git_pull", "description": "Pull changes"}
        ]
    }
    return tools


@router.post("/validate")
async def validate_tool_request(request: ToolRequest) -> dict:
    """
    Validate a tool request without executing.
    
    Args:
        request: ToolRequest to validate
        
    Returns:
        Validation result
    """
    try:
        is_valid = True
        errors = []
        
        # Basic validation
        if not request.tool:
            is_valid = False
            errors.append("Tool type is required")
        
        if not request.parameters:
            is_valid = False
            errors.append("Parameters are required")
        
        return {
            "valid": is_valid,
            "errors": errors,
            "tool": request.tool.value if request.tool else None,
            "parameters": request.parameters
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
