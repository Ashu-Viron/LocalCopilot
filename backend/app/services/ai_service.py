"""AI Service for FreeTheAI API integration with 16,000+ models."""

from openai import OpenAI
from typing import List, Dict, Optional, Generator
import os

from app.utils.logger import logger
from app.config import settings


class AIService:
    """Service for AI model interactions via FreeTheAI API."""
    
    # Top 10 models by successful request count
    AVAILABLE_MODELS = {
        "claude-sonnet": "rev/claude-sonnet-4.5",
        "glm-5.1": "glm/glm-5.1",
        "glm-5.1-org": "bbg/zai-org/GLM-5.1",
        "deepseek-v4-pro": "bbg/deepseek-ai/DeepSeek-V4-Pro",
        "gemini-3.0-flash": "bbl/gemini-3.0-flash",
        "gemini-2.5-flash": "bbl/gemini-2.5-flash",
        "deepseek-v4-flash": "bbg/deepseek-ai/DeepSeek-V4-Flash",
        "gpt-5.4-mini": "bbl/gpt-5.4-mini",
        "minimax-m2.5-free": "opc/minimax-m2.5-free",
        "glm-5": "bbg/zai-org/GLM-5"
    }
    
    # Fallback order if the primary model fails or is too slow.
    # Placed fast/reliable models first.
    FALLBACK_MODELS = [
        "glm/glm-5.1",
        "bbl/gemini-3.0-flash",
        "bbg/deepseek-ai/DeepSeek-V4-Pro",
        "bbl/gemini-2.5-flash",
        "bbg/zai-org/GLM-5.1",
        "bbl/gpt-5.4-mini",
        "bbg/deepseek-ai/DeepSeek-V4-Flash",
        "opc/minimax-m2.5-free",
        "bbg/zai-org/GLM-5",
        "rev/claude-sonnet-4.5"
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.freetheai.xyz/v1",
        default_model: str = "glm-5.1"
    ):
        """
        Initialize AI Service.
        
        Args:
            api_key: FreeTheAI API key
            base_url: API base URL
            default_model: Default model to use
        """
        # Use provided values or fall back to settings/env
        self.api_key = api_key or settings.FREETHEAI_API_KEY or ""
        self.base_url = base_url or settings.FREETHEAI_BASE_URL
        self.default_model = default_model or settings.LLM_MODEL
        
        if not self.api_key:
            logger.warning("FREETHEAI_API_KEY not configured. Get one at: https://discord.gg/secrets")
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        
        logger.info(f"AI Service initialized with model: {self.default_model}")
    
    def get_model_id(self, model_name: str) -> str:
        """
        Get full model ID.
        
        Args:
            model_name: Short model name or full model ID
            
        Returns:
            Full model ID (e.g., yng/gemini-3-1-pro)
        """
        # If already has FreeTheAI prefix, return as-is
        if "/" in model_name:
            return model_name
        
        # Look up in available models
        return self.AVAILABLE_MODELS.get(model_name, model_name)
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        Generate chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (optional, uses default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        primary_model = self.get_model_id(model or self.default_model)
        models_to_try = [primary_model] + [m for m in self.FALLBACK_MODELS if m != primary_model]
        last_error = None
        
        for current_model in models_to_try:
            try:
                logger.debug(f"Calling AI with model: {current_model}")
                
                # Add a timeout to fail fast if the free model is hanging
                kwargs_with_timeout = dict(kwargs)
                kwargs_with_timeout.setdefault('timeout', 60.0)
                
                completion = self.client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs_with_timeout
                )
                
                response = completion.choices[0].message.content
                logger.debug(f"AI response received from {current_model}: {len(response)} chars")
                
                return response
                
            except Exception as e:
                logger.warning(f"Model {current_model} failed ({e}). Switching to next fallback model...")
                last_error = e
                
        logger.error(f"All fallback models failed. Last error: {last_error}")
        raise AIServiceError(f"Failed to generate response after trying multiple free models. Last error: {last_error}")
    
    def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Generate streaming chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (optional, uses default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Response text chunks
        """
        primary_model = self.get_model_id(model or self.default_model)
        models_to_try = [primary_model] + [m for m in self.FALLBACK_MODELS if m != primary_model]
        last_error = None
        
        for current_model in models_to_try:
            has_yielded = False
            try:
                logger.debug(f"Streaming AI with model: {current_model}")
                
                kwargs_with_timeout = dict(kwargs)
                kwargs_with_timeout.setdefault('timeout', 60.0)
                
                stream = self.client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    **kwargs_with_timeout
                )
                
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        has_yielded = True
                        yield chunk.choices[0].delta.content
                
                # If we made it here successfully without exceptions, we are done
                return
                    
            except Exception as e:
                logger.warning(f"Model {current_model} failed streaming ({e}).")
                last_error = e
                
                # If we already yielded some content and it breaks midway, we shouldn't switch models
                # because the UI already started printing the output.
                if has_yielded:
                    logger.error(f"Stream interrupted midway for {current_model}")
                    raise AIServiceError(f"Stream interrupted: {e}")
                else:
                    logger.info("No content yielded yet, trying next fallback model...")
                    
        logger.error(f"All fallback models failed for streaming. Last error: {last_error}")
        raise AIServiceError(f"Failed to stream response after trying multiple models. Last error: {last_error}")
    
    async def async_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        Async wrapper for chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (optional, uses default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        # OpenAI client is sync, so we call it directly
        # For true async, consider using httpx or aiohttp
        return self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    def simple_chat(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Simple single-turn chat.
        
        Args:
            prompt: User prompt
            model: Model to use
            
        Returns:
            AI response
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(messages, model=model)
    
    def list_models(self) -> Dict[str, str]:
        """Get available models."""
        return self.AVAILABLE_MODELS.copy()


class AIServiceError(Exception):
    """Custom exception for AI service errors."""
    pass


# Global AI service instance
ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create AI service instance."""
    global ai_service
    
    if ai_service is None:
        ai_service = AIService()
    
    return ai_service


def init_ai_service(api_key: str, default_model: str = "gemini-2.5-flash-lite") -> AIService:
    """
    Initialize AI service with configuration.
    
    Args:
        api_key: A4F API key
        default_model: Default model to use
        
    Returns:
        Configured AIService instance
    """
    global ai_service
    
    ai_service = AIService(api_key=api_key, default_model=default_model)
    return ai_service
