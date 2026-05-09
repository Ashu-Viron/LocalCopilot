"""System and information API endpoints."""

from fastapi import APIRouter
from datetime import datetime

from app.config import settings

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
async def system_status() -> dict:
    """
    Get system status.
    
    Returns:
        System status information
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "debug": settings.DEBUG
    }


@router.get("/config")
async def get_config() -> dict:
    """
    Get system configuration (non-sensitive).
    
    Returns:
        Configuration information
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "workspace": str(settings.workspace_dir),
        "max_iterations": settings.MAX_ITERATIONS,
        "timeout_seconds": settings.TIMEOUT_SECONDS,
        "llm_model": settings.LLM_MODEL,
        "debug": settings.DEBUG
    }


@router.get("/workspace")
async def get_workspace_info() -> dict:
    """
    Get workspace information.
    
    Returns:
        Workspace information
    """
    workspace_dir = settings.workspace_dir
    try:
        files_count = sum(1 for _ in workspace_dir.rglob('*') if _.is_file())
        dirs_count = sum(1 for _ in workspace_dir.rglob('*') if _.is_dir())
        
        return {
            "path": str(workspace_dir),
            "exists": workspace_dir.exists(),
            "files_count": files_count,
            "directories_count": dirs_count,
            "accessible": workspace_dir.exists() and workspace_dir.is_dir()
        }
    except Exception as e:
        return {
            "path": str(workspace_dir),
            "exists": workspace_dir.exists(),
            "error": str(e)
        }


@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/version")
async def get_version() -> dict:
    """
    Get version information.
    
    Returns:
        Version info
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "python_version": "3.8+",
        "api_version": "v1"
    }


@router.post("/shutdown")
async def shutdown() -> dict:
    """
    Graceful shutdown (development only).
    
    Returns:
        Shutdown confirmation
    """
    if not settings.DEBUG:
        return {"error": "Shutdown only allowed in debug mode"}
    
    return {
        "message": "Shutdown initiated",
        "timestamp": datetime.utcnow().isoformat()
    }
