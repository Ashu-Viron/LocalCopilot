"""File operations API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.file_models import (
    DirectoryListing, FileReadResponse, FileEditResponse,
    FileEditRequest, FileCreateRequest, FileDeleteRequest,
    SearchRequest, SearchResponse
)
from app.tools import file_tools, search_tools

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/list", response_model=DirectoryListing)
async def list_files(path: str = Query(".", description="Directory path")) -> DirectoryListing:
    """
    List files in a directory.
    
    Args:
        path: Directory path relative to workspace
        
    Returns:
        DirectoryListing
    """
    try:
        result = await file_tools.list_directory(path)
        if not result:
            raise HTTPException(status_code=404, detail="Directory not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/read", response_model=FileReadResponse)
async def read_file(path: str = Query(..., description="File path")) -> FileReadResponse:
    """
    Read file contents.
    
    Args:
        path: File path relative to workspace
        
    Returns:
        FileReadResponse with content
    """
    try:
        result = await file_tools.read_file(path)
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/write", response_model=FileEditResponse)
async def write_file(request: FileEditRequest) -> FileEditResponse:
    """
    Write content to a file.
    
    Args:
        request: FileEditRequest with path and content
        
    Returns:
        FileEditResponse
    """
    try:
        result = await file_tools.write_file(
            request.path,
            request.content,
            request.backup
        )
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Write failed"))
        return FileEditResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=FileEditResponse)
async def create_file(request: FileCreateRequest) -> FileEditResponse:
    """
    Create a new file.
    
    Args:
        request: FileCreateRequest
        
    Returns:
        FileEditResponse
    """
    try:
        result = await file_tools.create_file(request.path, request.content)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Create failed"))
        return FileEditResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete", response_model=FileEditResponse)
async def delete_file(request: FileDeleteRequest) -> FileEditResponse:
    """
    Delete a file.
    
    Args:
        request: FileDeleteRequest
        
    Returns:
        FileEditResponse
    """
    try:
        result = await file_tools.delete_file(request.path, request.backup)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Delete failed"))
        return FileEditResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_files(request: SearchRequest) -> SearchResponse:
    """
    Search for pattern in files.
    
    Args:
        request: SearchRequest
        
    Returns:
        SearchResponse with results
    """
    try:
        result = await search_tools.search_files(
            request.pattern,
            request.path,
            request.is_regex,
            request.case_sensitive
        )
        if not result:
            return SearchResponse(pattern=request.pattern, results=[], total_matches=0)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_file_info(path: str = Query(..., description="File path")) -> dict:
    """
    Get file information.
    
    Args:
        path: File path relative to workspace
        
    Returns:
        File information
    """
    try:
        result = await file_tools.get_file_info(path)
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        return result.dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
