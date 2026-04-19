"""
Centralized configuration management.

This module defines the application configuration system using
Pydantic-based settings with layered sources.

Configuration priority (highest → lowest):
    1. Initialization arguments
    2. OS environment variables
    3. .env file (only in DEV)
    4. YAML configuration file
    5. Default values

The design ensures:
    - Deterministic resolution order
    - Environment-aware behavior (DEV vs PROD)
    - Type validation and early failure
    - Compatibility with dependency injection patterns
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Root directory of the project (resolved dynamically)
BASE_DIR = Path(__file__).resolve().parents[2]

# Execution environment (e.g., DEV, PROD)
ENV = os.getenv("LEXRAG_ENV", "DEV").upper()


def load_yaml() -> Dict[str, Any]:
    """Load configuration from YAML file.

    Returns:
        Dict[str, Any]: Parsed YAML configuration. Returns empty dict if file is missing.

    Notes:
        - This function does not raise if the file is absent.
        - YAML is treated as a low-priority configuration source.
    """
    path = BASE_DIR / "config.yaml"

    if not path.exists():
        return {}

    with path.open("r") as f:
        return yaml.safe_load(f) or {}



class Settings(BaseSettings):
    """Application configuration.

    Attributes:
        DB_URL (str): Database connection string.
        API_KEY (str): External service API key.
        TIMEOUT (int): Request timeout in seconds.
        yaml_config (Dict[str, Any]): Raw YAML configuration for advanced use cases.

    Behavior:
        - Validates required environment variables at initialization.
        - Applies layered configuration resolution.
        - Avoids runtime mutation for predictability.
    """

    # -------- Core configuration --------
    DB_URL: str = Field(..., description="Database connection URL")
    API_KEY: str = Field(..., description="API key for external services")

    # -------- Defaults --------
    TIMEOUT: int = Field(
        default=30,
        description="Request timeout in seconds",
        ge=0,
    )

    # -------- Raw YAML (non-authoritative) --------
    yaml_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw YAML configuration data",
    )

    # -------- Pydantic settings configuration --------
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env" if ENV == "DEV" else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """Customize configuration source priority.

        Args:
            settings_cls: Settings class reference.
            init_settings: Values passed during initialization.
            env_settings: OS environment variables.
            dotenv_settings: Values loaded from .env file.
            file_secret_settings: File-based secret providers.

        Returns:
            Tuple of callables representing configuration sources in priority order.
        """
        yaml_data = load_yaml()

        # Extract relevant YAML fields into flat structure
        yaml_mapped = {
            "TIMEOUT": yaml_data.get("service", {}).get("timeout"),
        }

        def yaml_source() -> Dict[str, Any]:
            """Provide YAML-derived configuration values."""
            return {
                key: value
                for key, value in yaml_mapped.items()
                if value is not None
            }

        return (
            init_settings,
            env_settings,
            dotenv_settings,
            yaml_source,
            file_secret_settings,
        )

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook.

        Attaches raw YAML configuration for optional downstream usage.

        Args:
            __context: Internal Pydantic context (unused).
        """
        object.__setattr__(self, "yaml_config", load_yaml())