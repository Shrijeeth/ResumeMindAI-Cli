"""
Base classes and enums for LLM providers
"""

from enum import Enum


class ProviderType(Enum):
    """Enumeration of supported LLM provider types"""

    GPT = "gpt"
    GEMINI = "gemini"
    CLAUDE = "claude"
    OLLAMA = "ollama"
    LITELLM = "litellm"
