"""
LLM provider abstraction supporting both cloud (OpenAI) and local models.
"""

from typing import Protocol, Any
from openai import AsyncOpenAI

from backend.config import settings
from backend.core.logger import get_logger

logger = get_logger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    
    async def create_completion(
        self, 
        messages: list[dict[str, str]], 
        **kwargs: Any
    ) -> str:
        """Create a completion from messages."""
        ...


class OpenAIProvider:
    """OpenAI cloud provider."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        logger.info("openai_provider_initialized")
        
    async def create_completion(
        self, 
        messages: list[dict[str, str]], 
        model: str = "gpt-4",
        **kwargs: Any
    ) -> str:
        """
        Create completion using OpenAI API.
        
        Args:
            messages: List of message dictionaries
            model: Model to use
            **kwargs: Additional parameters for API call
            
        Returns:
            Completion text
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("openai_completion_failed", error=str(e))
            raise


class LocalModelProvider:
    """Local model provider using transformers."""
    
    def __init__(self):
        # Placeholder for local model implementation
        logger.warning(
            "local_provider_stub",
            message="Local model provider not fully implemented"
        )
        
    async def create_completion(
        self, 
        messages: list[dict[str, str]], 
        **kwargs: Any
    ) -> str:
        """
        Create completion using local model.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters
            
        Returns:
            Completion text
        """
        # TODO: Implement local model inference
        raise NotImplementedError("Local model provider not yet implemented")


def get_llm_provider() -> LLMProvider:
    """
    Get the appropriate LLM provider based on configuration.
    
    Returns:
        Configured LLM provider instance
    """
    if settings.llm_inference_mode == "cloud":
        return OpenAIProvider()
    elif settings.llm_inference_mode == "local":
        return LocalModelProvider()
    else:
        raise ValueError(f"Invalid LLM mode: {settings.llm_inference_mode}")

