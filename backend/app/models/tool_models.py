"""Pydantic models for tool execution."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ToolType(str, Enum):
    """Available tool types."""
    FILE_READ = "read_file"
    FILE_WRITE = "edit_file"
    FILE_CREATE = "create_file"
    FILE_DELETE = "delete_file"
    FILE_LIST = "list_files"
    SEARCH = "search_files"
    RUN_COMMAND = "run_command"
    GIT_STATUS = "git_status"
    GIT_COMMIT = "git_commit"
    GIT_DIFF = "git_diff"


class ToolRequest(BaseModel):
    """Request to execute a tool."""
    
    tool: ToolType = Field(..., description="Tool to execute")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters")
    timeout: Optional[int] = Field(default=30, description="Execution timeout in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "tool": "read_file",
                "parameters": {"path": "src/auth.js"},
                "timeout": 30
            }
        }


class ToolExecution(BaseModel):
    """Record of a tool execution."""
    
    id: str = Field(..., description="Execution ID")
    tool: ToolType = Field(..., description="Tool executed")
    parameters: Dict[str, Any] = Field(..., description="Parameters used")
    status: str = Field(..., description="Status: 'pending', 'running', 'success', 'error'")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = Field(None)
    duration: Optional[float] = Field(None, description="Execution duration in seconds")


class ToolResult(BaseModel):
    """Result from tool execution."""
    
    id: str = Field(..., description="Execution ID")
    tool: ToolType = Field(..., description="Tool executed")
    success: bool = Field(..., description="Whether execution was successful")
    output: Any = Field(..., description="Tool output/result")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time: float = Field(..., description="Execution time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "exec_123",
                "tool": "read_file",
                "success": True,
                "output": {"content": "function login() { ... }"},
                "error": None,
                "execution_time": 0.05
            }
        }


class CommandRequest(BaseModel):
    """Request to run a shell command."""
    
    command: str = Field(..., description="Command to execute")
    cwd: Optional[str] = Field(None, description="Working directory")
    timeout: int = Field(default=30, description="Timeout in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "command": "npm test",
                "cwd": ".",
                "timeout": 60
            }
        }


class CommandResult(BaseModel):
    """Result from command execution."""
    
    command: str = Field(..., description="Command executed")
    return_code: int = Field(..., description="Return code")
    stdout: str = Field(..., description="Standard output")
    stderr: str = Field(..., description="Standard error")
    duration: float = Field(..., description="Execution time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "command": "npm test",
                "return_code": 0,
                "stdout": "All tests passed",
                "stderr": "",
                "duration": 5.2
            }
        }


class DiffChange(BaseModel):
    """A single change in a diff."""
    
    type: str = Field(..., description="Change type: 'add', 'remove', 'modify'")
    line_number: int = Field(..., description="Line number")
    old_content: Optional[str] = Field(None, description="Original content")
    new_content: Optional[str] = Field(None, description="New content")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "modify",
                "line_number": 10,
                "old_content": "old code",
                "new_content": "new code"
            }
        }


class FileDiff(BaseModel):
    """Diff for a single file."""
    
    file_path: str = Field(..., description="File path")
    changes: List[DiffChange] = Field(..., description="List of changes")
    additions: int = Field(..., description="Number of additions")
    deletions: int = Field(..., description="Number of deletions")
    
    class Config:
        schema_extra = {
            "example": {
                "file_path": "src/auth.js",
                "changes": [],
                "additions": 3,
                "deletions": 2
            }
        }


class ToolLog(BaseModel):
    """A log entry from tool execution."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = Field(..., description="Log level: INFO, WARNING, ERROR, DEBUG")
    tool: Optional[ToolType] = Field(None, description="Tool that generated log")
    message: str = Field(..., description="Log message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2026-01-19T10:30:00",
                "level": "INFO",
                "tool": "read_file",
                "message": "File read successfully",
                "details": {"path": "src/auth.js"}
            }
        }
