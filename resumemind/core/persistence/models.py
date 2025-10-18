"""
Database models for provider persistence
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from ..providers.base import ProviderType
from ..providers.config import ProviderConfig


@dataclass
class ProviderModel:
    """Database model for provider configuration with embedding support"""

    id: Optional[int] = None
    name: str = ""
    provider_type: str = ""
    model: str = ""
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    additional_params: Optional[str] = None  # JSON string

    # Embedding configuration
    embedding_model: Optional[str] = None
    embedding_api_key_env: Optional[str] = None
    embedding_base_url: Optional[str] = None
    embedding_additional_params: Optional[str] = None  # JSON string

    is_active: bool = False
    is_default: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_provider_config(
        cls, config: ProviderConfig, is_active: bool = False, is_default: bool = False
    ) -> "ProviderModel":
        """Create ProviderModel from ProviderConfig"""
        additional_params_json = None
        if config.additional_params:
            additional_params_json = json.dumps(config.additional_params)

        embedding_additional_params_json = None
        if config.embedding_additional_params:
            embedding_additional_params_json = json.dumps(
                config.embedding_additional_params
            )

        return cls(
            name=config.name,
            provider_type=config.provider_type.value,
            model=config.model,
            api_key_env=config.api_key_env,
            base_url=config.base_url,
            additional_params=additional_params_json,
            embedding_model=config.embedding_model,
            embedding_api_key_env=config.embedding_api_key_env,
            embedding_base_url=config.embedding_base_url,
            embedding_additional_params=embedding_additional_params_json,
            is_active=is_active,
            is_default=is_default,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

    def to_provider_config(self) -> ProviderConfig:
        """Convert ProviderModel to ProviderConfig"""
        additional_params = None
        if self.additional_params:
            additional_params = json.loads(self.additional_params)

        embedding_additional_params = None
        if self.embedding_additional_params:
            embedding_additional_params = json.loads(self.embedding_additional_params)

        return ProviderConfig(
            name=self.name,
            provider_type=ProviderType(self.provider_type),
            model=self.model,
            api_key_env=self.api_key_env,
            base_url=self.base_url,
            additional_params=additional_params,
            embedding_model=self.embedding_model,
            embedding_api_key_env=self.embedding_api_key_env,
            embedding_base_url=self.embedding_base_url,
            embedding_additional_params=embedding_additional_params,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations"""
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "model": self.model,
            "api_key_env": self.api_key_env,
            "base_url": self.base_url,
            "additional_params": self.additional_params,
            "embedding_model": self.embedding_model,
            "embedding_api_key_env": self.embedding_api_key_env,
            "embedding_base_url": self.embedding_base_url,
            "embedding_additional_params": self.embedding_additional_params,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderModel":
        """Create ProviderModel from dictionary"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            provider_type=data.get("provider_type", ""),
            model=data.get("model", ""),
            api_key_env=data.get("api_key_env"),
            base_url=data.get("base_url"),
            additional_params=data.get("additional_params"),
            embedding_model=data.get("embedding_model"),
            embedding_api_key_env=data.get("embedding_api_key_env"),
            embedding_base_url=data.get("embedding_base_url"),
            embedding_additional_params=data.get("embedding_additional_params"),
            is_active=data.get("is_active", False),
            is_default=data.get("is_default", False),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
