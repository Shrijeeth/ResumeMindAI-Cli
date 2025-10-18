"""
LLM Provider registry and management - Simplified for LiteLLM only
"""

from typing import Any, Dict, Optional

from ..services.embedding_service import get_default_embedding_models
from .base import ProviderType
from .config import ProviderConfig


class LLMProviders:
    """Manages LLM provider configurations using LiteLLM - Custom configuration only"""

    @classmethod
    def create_custom_config(
        cls,
        model: str,
        api_key: str = None,
        base_url: str = None,
        embedding_model: Optional[str] = None,
        embedding_api_key: Optional[str] = None,
        embedding_base_url: Optional[str] = None,
    ) -> tuple[ProviderConfig, Dict[str, Any]]:
        """Create a custom model configuration with embedding support"""

        # Auto-select embedding model if not provided
        if not embedding_model:
            default_models = get_default_embedding_models()
            if "ollama" in model.lower():
                embedding_model = default_models["ollama"]
            elif "gpt" in model.lower() or "openai" in model.lower():
                embedding_model = default_models["openai"]
            elif "gemini" in model.lower():
                embedding_model = default_models["gemini"]
            elif "claude" in model.lower():
                embedding_model = default_models["claude"]
            else:
                embedding_model = default_models["custom"]

        # Use same credentials for embedding if not specified
        if not embedding_api_key:
            embedding_api_key = api_key
        if not embedding_base_url:
            embedding_base_url = base_url

        config = ProviderConfig(
            name=f"Custom {model}",
            provider_type=ProviderType.LITELLM,
            model=model,
            base_url=base_url if base_url else None,
            api_key_env=api_key if api_key else None,
            embedding_model=embedding_model,
            embedding_api_key_env=embedding_api_key,
            embedding_base_url=embedding_base_url,
        )

        litellm_config = {"model": model}
        if api_key:
            litellm_config["api_key"] = api_key
        if base_url:
            litellm_config["api_base"] = base_url

        return config, litellm_config

    @classmethod
    def get_embedding_model_examples(cls) -> Dict[str, list]:
        """Get embedding model examples for different providers"""
        return {
            "OpenAI": [
                "text-embedding-3-small",
                "text-embedding-3-large",
                "text-embedding-ada-002",
            ],
            "Ollama": [
                "ollama/nomic-embed-text",
                "ollama/mxbai-embed-large",
                "ollama/all-minilm",
            ],
            "Google": ["text-embedding-004", "text-embedding-gecko-001"],
            "Custom": [
                "text-embedding-3-small",  # Fallback
                "custom/your-embedding-model",
            ],
        }
