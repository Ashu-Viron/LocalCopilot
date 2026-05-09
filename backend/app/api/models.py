"""AI Models API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List

from app.services.ai_service import get_ai_service, AIServiceError
from app.utils.logger import logger

router = APIRouter(prefix="/api/models", tags=["models"])


class TestPromptRequest(BaseModel):
    """Request for testing AI prompt."""
    prompt: str
    model: Optional[str] = None


class TestPromptResponse(BaseModel):
    """Response from AI test."""
    response: str
    model: str


class ModelInfo(BaseModel):
    """Model information."""
    id: str
    name: str
    provider: str


@router.get("/available")
async def list_available_models() -> Dict[str, str]:
    """
    List available AI models.
    
    Returns:
        Dict of model names to full model IDs
    """
    try:
        ai_service = get_ai_service()
        return ai_service.list_models()
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current")
async def get_current_model() -> dict:
    """
    Get current default model.
    
    Returns:
        Current model info
    """
    try:
        ai_service = get_ai_service()
        return {
            "model": ai_service.default_model,
            "model_id": ai_service.get_model_id(ai_service.default_model)
        }
    except Exception as e:
        logger.error(f"Error getting current model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_prompt(request: TestPromptRequest) -> TestPromptResponse:
    """
    Test AI with a simple prompt.
    
    Args:
        request: Test prompt request
        
    Returns:
        AI response
    """
    try:
        ai_service = get_ai_service()
        
        model = request.model or ai_service.default_model
        response = ai_service.simple_chat(request.prompt, model=model)
        
        return TestPromptResponse(
            response=response,
            model=ai_service.get_model_id(model)
        )
    except AIServiceError as e:
        logger.error(f"AI test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in AI test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def check_ai_status() -> dict:
    """
    Check AI service status.
    
    Returns:
        Status info
    """
    try:
        ai_service = get_ai_service()
        
        # Quick test to see if API is working
        has_api_key = bool(ai_service.api_key)
        
        status = {
            "configured": has_api_key,
            "default_model": ai_service.default_model,
            "base_url": ai_service.base_url,
            "available_models": len(ai_service.list_models())
        }
        
        if has_api_key:
            try:
                # Quick connectivity test
                response = ai_service.simple_chat("Hello", model=ai_service.default_model)
                status["connected"] = True
                status["test_response"] = response[:100] + "..." if len(response) > 100 else response
            except Exception as e:
                status["connected"] = False
                status["error"] = str(e)
        else:
            status["connected"] = False
            status["error"] = "API key not configured"
        
        return status
        
    except Exception as e:
        logger.error(f"Error checking AI status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
