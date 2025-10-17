"""
LLM Provider registry and management
"""

import os
from typing import Any, Dict

from .base import ProviderType
from .config import ProviderConfig


class LLMProviders:
    """Manages LLM provider configurations"""

    PROVIDERS = {
        ProviderType.GPT: {
            "gpt-4": ProviderConfig(
                name="GPT-4",
                provider_type=ProviderType.GPT,
                model="gpt-4",
                api_key_env="OPENAI_API_KEY",
            ),
            "gpt-4-turbo": ProviderConfig(
                name="GPT-4 Turbo",
                provider_type=ProviderType.GPT,
                model="gpt-4-turbo",
                api_key_env="OPENAI_API_KEY",
            ),
            "gpt-3.5-turbo": ProviderConfig(
                name="GPT-3.5 Turbo",
                provider_type=ProviderType.GPT,
                model="gpt-3.5-turbo",
                api_key_env="OPENAI_API_KEY",
            ),
        },
        ProviderType.GEMINI: {
            "gemini-pro": ProviderConfig(
                name="Gemini Pro",
                provider_type=ProviderType.GEMINI,
                model="gemini/gemini-pro",
                api_key_env="GOOGLE_API_KEY",
            ),
            "gemini-1.5-pro": ProviderConfig(
                name="Gemini 1.5 Pro",
                provider_type=ProviderType.GEMINI,
                model="gemini/gemini-1.5-pro",
                api_key_env="GOOGLE_API_KEY",
            ),
        },
        ProviderType.CLAUDE: {
            "claude-3-opus": ProviderConfig(
                name="Claude 3 Opus",
                provider_type=ProviderType.CLAUDE,
                model="claude-3-opus-20240229",
                api_key_env="ANTHROPIC_API_KEY",
            ),
            "claude-3-sonnet": ProviderConfig(
                name="Claude 3 Sonnet",
                provider_type=ProviderType.CLAUDE,
                model="claude-3-sonnet-20240229",
                api_key_env="ANTHROPIC_API_KEY",
            ),
            "claude-3-haiku": ProviderConfig(
                name="Claude 3 Haiku",
                provider_type=ProviderType.CLAUDE,
                model="claude-3-haiku-20240307",
                api_key_env="ANTHROPIC_API_KEY",
            ),
        },
        ProviderType.OLLAMA: {
            "llama2": ProviderConfig(
                name="Llama 2 (Ollama)",
                provider_type=ProviderType.OLLAMA,
                model="ollama/llama2",
                base_url="http://localhost:11434",
            ),
            "codellama": ProviderConfig(
                name="Code Llama (Ollama)",
                provider_type=ProviderType.OLLAMA,
                model="ollama/codellama",
                base_url="http://localhost:11434",
            ),
            "mistral": ProviderConfig(
                name="Mistral (Ollama)",
                provider_type=ProviderType.OLLAMA,
                model="ollama/mistral",
                base_url="http://localhost:11434",
            ),
        },
    }

    @classmethod
    def get_providers_by_type(
        cls, provider_type: ProviderType
    ) -> Dict[str, ProviderConfig]:
        """Get all providers of a specific type"""
        return cls.PROVIDERS.get(provider_type, {})

    @classmethod
    def get_all_providers(cls) -> Dict[str, ProviderConfig]:
        """Get all available providers as a flat dictionary"""
        all_providers = {}
        for provider_dict in cls.PROVIDERS.values():
            all_providers.update(provider_dict)
        return all_providers

    @classmethod
    def validate_provider_config(cls, config: ProviderConfig) -> bool:
        """Validate if a provider configuration is complete"""
        if config.api_key_env and not os.getenv(config.api_key_env):
            return False
        return True

    @classmethod
    def create_litellm_config(cls, config: ProviderConfig) -> Dict[str, Any]:
        """Create LiteLLM configuration from provider config"""
        litellm_config = {"model": config.model}

        if config.api_key_env and os.getenv(config.api_key_env):
            litellm_config["api_key"] = os.getenv(config.api_key_env)

        if config.base_url:
            litellm_config["api_base"] = config.base_url

        if config.additional_params:
            litellm_config.update(config.additional_params)

        return litellm_config
