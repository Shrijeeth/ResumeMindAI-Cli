"""
LLM Provider registry and management - Simplified for LiteLLM only
"""

from typing import Any, Dict

from .base import ProviderType
from .config import ProviderConfig


class LLMProviders:
    """Manages LLM provider configurations using LiteLLM - Custom configuration only"""

    @classmethod
    def create_custom_config(
        cls, model: str, api_key: str = None, base_url: str = None
    ) -> tuple[ProviderConfig, Dict[str, Any]]:
        """Create a custom model configuration"""
        config = ProviderConfig(
            name=f"Custom {model}",
            provider_type=ProviderType.LITELLM,
            model=model,
            base_url=base_url if base_url else None,
        )

        litellm_config = {"model": model}
        if api_key:
            litellm_config["api_key"] = api_key
        if base_url:
            litellm_config["api_base"] = base_url

        return config, litellm_config
