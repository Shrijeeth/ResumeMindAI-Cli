"""
Base classes and enums for LLM providers - Simplified for LiteLLM only
"""

from enum import Enum


class ProviderType(Enum):
    """Enumeration of supported LLM provider types"""

    LITELLM = "litellm"
