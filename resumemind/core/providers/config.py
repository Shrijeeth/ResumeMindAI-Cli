"""
Provider configuration data classes
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .base import ProviderType


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider with embedding support"""

    name: str
    provider_type: ProviderType
    model: str
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None

    # Embedding configuration
    embedding_model: Optional[str] = None
    embedding_api_key_env: Optional[str] = None
    embedding_base_url: Optional[str] = None
    embedding_additional_params: Optional[Dict[str, Any]] = None
