"""
Provider configuration data classes
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .base import ProviderType


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider"""

    name: str
    provider_type: ProviderType
    model: str
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None
