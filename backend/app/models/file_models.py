"""Pydantic models for file operations."""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class FileInfo(BaseModel):
    """Information about a file."""
    
    path: str = Field(..., description="File path relative to workspace")
    name: str = Field(..., description="File name")
    is_file: bool = Field(..., description="Is this a file or directory")
    size: Optional[int] = Field(None, description="File size in bytes")
    modified_at: Optional[datetime] = Field(None, description="Last modified time")
    
    class Config:
        schema_extra = {
            "example": {
                "path": "src/auth.js",
                "name": "auth.js",
                "is_file": True,
                "size": 2048,
                "modified_at": "2026-01-19T10:00:00"
            }
        }


class DirectoryListing(BaseModel):
    """Directory listing response."""
    
    path: str = Field(..., description="Directory path")
    files: List[FileInfo] = Field(..., description="Files in directory")
    total_count: int = Field(..., description="Total number of items")
    
    class Config:
        schema_extra = {
            "example": {
                "path": "src/",
                "files": [
                    {"path": "src/auth.js", "name": "auth.js", "is_file": True}
                ],
                "total_count": 1
            }
        }


class FileReadRequest(BaseModel):
    """Request to read a file."""
    
    path: str = Field(..., description="File path relative to workspace")
    
    class Config:
        schema_extra = {
            "example": {"path": "src/auth.js"}
        }


class FileReadResponse(BaseModel):
    """Response with file content."""
    
    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
    size: int = Field(..., description="File size in bytes")
    encoding: str = Field(default="utf-8", description="File encoding")
    lines: int = Field(..., description="Number of lines")
    
    class Config:
        schema_extra = {
            "example": {
                "path": "src/auth.js",
                "content": "function login() { ... }",
                "size": 2048,
                "encoding": "utf-8",
                "lines": 42
            }
        }


class FileEditRequest(BaseModel):
    """Request to edit a file."""
    
    path: str = Field(..., description="File path relative to workspace")
    content: str = Field(..., description="New file content")
    backup: bool = Field(default=True, description="Create backup before editing")
    
    class Config:
        schema_extra = {
            "example": {
                "path": "src/auth.js",
                "content": "function login() { fixed... }",
                "backup": True
            }
        }


class FileEditResponse(BaseModel):
    """Response from file edit."""
    
    path: str = Field(..., description="File path")
    success: bool = Field(..., description="Whether edit was successful")
    message: str = Field(..., description="Status message")
    backup_path: Optional[str] = Field(None, description="Path to backup if created")
    lines_changed: int = Field(default=0, description="Number of lines changed")
    
    class Config:
        schema_extra = {
            "example": {
                "path": "src/auth.js",
                "success": True,
                "message": "File updated successfully",
                "backup_path": "src/auth.js.bak",
                "lines_changed": 5
            }
        }


class FileCreateRequest(BaseModel):
    """Request to create a new file."""
    
    path: str = Field(..., description="File path relative to workspace")
    content: str = Field(default="", description="Initial file content")
    
    class Config:
        schema_extra = {
            "example": {
                "path": "src/newfile.js",
                "content": "// New file"
            }
        }


class FileDeleteRequest(BaseModel):
    """Request to delete a file."""
    
    path: str = Field(..., description="File path relative to workspace")
    backup: bool = Field(default=True, description="Create backup before deleting")
    
    class Config:
        schema_extra = {
            "example": {
                "path": "src/oldfile.js",
                "backup": True
            }
        }


class SearchRequest(BaseModel):
    """Request to search files."""
    
    pattern: str = Field(..., description="Search pattern (regex or text)")
    path: Optional[str] = Field(None, description="Search within path")
    is_regex: bool = Field(default=False, description="Use regex pattern")
    case_sensitive: bool = Field(default=False, description="Case sensitive search")
    
    class Config:
        schema_extra = {
            "example": {
                "pattern": "function login",
                "path": "src/",
                "is_regex": False,
                "case_sensitive": False
            }
        }


class SearchResult(BaseModel):
    """Single search result."""
    
    file_path: str = Field(..., description="File where match was found")
    line_number: int = Field(..., description="Line number of match")
    content: str = Field(..., description="Line content")
    
    class Config:
        schema_extra = {
            "example": {
                "file_path": "src/auth.js",
                "line_number": 5,
                "content": "function login() {"
            }
        }


class SearchResponse(BaseModel):
    """Response from file search."""
    
    pattern: str = Field(..., description="Search pattern used")
    results: List[SearchResult] = Field(..., description="Search results")
    total_matches: int = Field(..., description="Total number of matches")
    
    class Config:
        schema_extra = {
            "example": {
                "pattern": "function login",
                "results": [
                    {"file_path": "src/auth.js", "line_number": 5, "content": "function login() {"}
                ],
                "total_matches": 1
            }
        }
