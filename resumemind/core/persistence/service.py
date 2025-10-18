"""
Provider state management service using SQLite
"""

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from ..providers.config import ProviderConfig
from .models import ProviderModel


class ProviderStateService:
    """Service for managing provider state persistence"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the service"""
        if hasattr(self, "_initialized"):
            return

        self.db_path = Path.home() / ".resumemind" / "providers.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self._initialized = True
        self._init_database()

    def _init_database(self):
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    provider_type TEXT NOT NULL,
                    model TEXT NOT NULL,
                    api_key_env TEXT,
                    base_url TEXT,
                    additional_params TEXT,
                    embedding_model TEXT,
                    embedding_api_key_env TEXT,
                    embedding_base_url TEXT,
                    embedding_additional_params TEXT,
                    is_active BOOLEAN DEFAULT FALSE,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Add embedding columns to existing tables (migration)
            try:
                conn.execute("ALTER TABLE providers ADD COLUMN embedding_model TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute(
                    "ALTER TABLE providers ADD COLUMN embedding_api_key_env TEXT"
                )
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute("ALTER TABLE providers ADD COLUMN embedding_base_url TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute(
                    "ALTER TABLE providers ADD COLUMN embedding_additional_params TEXT"
                )
            except sqlite3.OperationalError:
                pass  # Column already exists

            # Create index for faster lookups
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_providers_active ON providers(is_active)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_providers_default ON providers(is_default)"
            )
            conn.commit()

    def save_provider(
        self, config: ProviderConfig, is_active: bool = False, is_default: bool = False
    ) -> int:
        """
        Save a provider configuration to the database

        Args:
            config: Provider configuration to save
            is_active: Whether this provider is currently active
            is_default: Whether this provider should be the default

        Returns:
            The ID of the saved provider
        """
        provider_model = ProviderModel.from_provider_config(
            config, is_active, is_default
        )

        with sqlite3.connect(self.db_path) as conn:
            # If setting as default, unset other defaults
            if is_default:
                conn.execute("UPDATE providers SET is_default = FALSE")

            # If setting as active, unset other active providers
            if is_active:
                conn.execute("UPDATE providers SET is_active = FALSE")

            # Check if provider with same name exists
            existing = conn.execute(
                "SELECT id FROM providers WHERE name = ?", (provider_model.name,)
            ).fetchone()

            if existing:
                # Update existing provider
                provider_model.id = existing[0]
                provider_model.updated_at = datetime.now().isoformat()

                conn.execute(
                    """
                    UPDATE providers SET 
                        provider_type = ?, model = ?, api_key_env = ?, base_url = ?,
                        additional_params = ?, embedding_model = ?, embedding_api_key_env = ?,
                        embedding_base_url = ?, embedding_additional_params = ?,
                        is_active = ?, is_default = ?, updated_at = ?
                    WHERE id = ?
                """,
                    (
                        provider_model.provider_type,
                        provider_model.model,
                        provider_model.api_key_env,
                        provider_model.base_url,
                        provider_model.additional_params,
                        provider_model.embedding_model,
                        provider_model.embedding_api_key_env,
                        provider_model.embedding_base_url,
                        provider_model.embedding_additional_params,
                        provider_model.is_active,
                        provider_model.is_default,
                        provider_model.updated_at,
                        provider_model.id,
                    ),
                )

                return provider_model.id
            else:
                # Insert new provider
                cursor = conn.execute(
                    """
                    INSERT INTO providers 
                    (name, provider_type, model, api_key_env, base_url, additional_params,
                     embedding_model, embedding_api_key_env, embedding_base_url, embedding_additional_params,
                     is_active, is_default, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        provider_model.name,
                        provider_model.provider_type,
                        provider_model.model,
                        provider_model.api_key_env,
                        provider_model.base_url,
                        provider_model.additional_params,
                        provider_model.embedding_model,
                        provider_model.embedding_api_key_env,
                        provider_model.embedding_base_url,
                        provider_model.embedding_additional_params,
                        provider_model.is_active,
                        provider_model.is_default,
                        provider_model.created_at,
                        provider_model.updated_at,
                    ),
                )

                return cursor.lastrowid

    def get_all_providers(self) -> List[ProviderModel]:
        """Get all saved providers"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM providers ORDER BY is_default DESC, is_active DESC, updated_at DESC
            """)

            return [ProviderModel.from_dict(dict(row)) for row in cursor.fetchall()]

    def get_active_provider(self) -> Optional[ProviderModel]:
        """Get the currently active provider"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM providers WHERE is_active = TRUE LIMIT 1"
            )
            row = cursor.fetchone()

            if row:
                return ProviderModel.from_dict(dict(row))
            return None

    def get_default_provider(self) -> Optional[ProviderModel]:
        """Get the default provider"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM providers WHERE is_default = TRUE LIMIT 1"
            )
            row = cursor.fetchone()

            if row:
                return ProviderModel.from_dict(dict(row))
            return None

    def get_provider_by_id(self, provider_id: int) -> Optional[ProviderModel]:
        """Get a provider by its ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM providers WHERE id = ?", (provider_id,)
            )
            row = cursor.fetchone()

            if row:
                return ProviderModel.from_dict(dict(row))
            return None

    def get_provider_by_name(self, name: str) -> Optional[ProviderModel]:
        """Get a provider by its name"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM providers WHERE name = ?", (name,))
            row = cursor.fetchone()

            if row:
                return ProviderModel.from_dict(dict(row))
            return None

    def set_active_provider(self, provider_id: int) -> bool:
        """Set a provider as active"""
        with sqlite3.connect(self.db_path) as conn:
            # First, unset all active providers
            conn.execute("UPDATE providers SET is_active = FALSE")

            # Set the specified provider as active
            cursor = conn.execute(
                "UPDATE providers SET is_active = TRUE, updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), provider_id),
            )

            return cursor.rowcount > 0

    def set_default_provider(self, provider_id: int) -> bool:
        """Set a provider as default"""
        with sqlite3.connect(self.db_path) as conn:
            # First, unset all default providers
            conn.execute("UPDATE providers SET is_default = FALSE")

            # Set the specified provider as default
            cursor = conn.execute(
                "UPDATE providers SET is_default = TRUE, updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), provider_id),
            )

            return cursor.rowcount > 0

    def delete_provider(self, provider_id: int) -> bool:
        """Delete a provider"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM providers WHERE id = ?", (provider_id,))
            return cursor.rowcount > 0

    def get_provider_config_and_litellm(
        self, provider_id: int
    ) -> Optional[Tuple[ProviderConfig, dict]]:
        """Get provider configuration and LiteLLM config for a provider"""
        provider_model = self.get_provider_by_id(provider_id)
        if not provider_model:
            return None

        config = provider_model.to_provider_config()

        # Create LiteLLM config
        litellm_config = {"model": config.model}
        if config.api_key_env:
            litellm_config["api_key"] = config.api_key_env
        if config.base_url:
            litellm_config["api_base"] = config.base_url
        if config.additional_params:
            litellm_config.update(config.additional_params)

        return config, litellm_config

    def has_providers(self) -> bool:
        """Check if any providers are saved"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM providers")
            count = cursor.fetchone()[0]
            return count > 0

    def clear_all_providers(self) -> int:
        """Clear all providers from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM providers")
            return cursor.rowcount
