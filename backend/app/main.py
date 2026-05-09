"""Main FastAPI application for AI Workspace."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from app.config import settings
from app.utils.logger import logger

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered coding assistant for local development",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

# Info endpoint
@app.get("/info")
async def get_info():
    """Get application information."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "workspace": str(settings.workspace_dir),
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }

# Validate workspace on startup
@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    if settings.validate_workspace():
        logger.info(f"Workspace validated: {settings.workspace_dir}")
    else:
        logger.error("Failed to validate workspace")
    
    # Initialize database (optional - continue if it fails)
    try:
        from app.database.connection import init_db
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization skipped (optional): {type(e).__name__}")
        logger.debug(f"Database error details: {e}")
    
    # Initialize AI service
    from app.services.ai_service import init_ai_service
    api_key = settings.FREETHEAI_API_KEY or settings.A4F_API_KEY
    if api_key:
        init_ai_service(
            api_key=api_key,
            default_model=settings.LLM_MODEL
        )
        logger.info(f"AI service initialized with model: {settings.LLM_MODEL}")
    else:
        logger.warning("API key not configured - AI features will be limited")
    
    logger.info("Application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Application shutting down")

# Include routers
from app.api import chat, files, tools, system, models, terminal
app.include_router(chat.router)
app.include_router(files.router)
app.include_router(tools.router)
app.include_router(system.router)
app.include_router(models.router)
app.include_router(terminal.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
