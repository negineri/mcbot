"""Configuration module for the application."""

import logging
from collections.abc import Callable
from os.path import expanduser
from pathlib import Path
from typing import Any

import tomli
from injector import Binder
from pydantic import BaseModel, Field
from pydantic.v1.utils import deep_update

from mcbot.env import APP_NAME, ENV_PREFIX
from mcbot.modules.common import CommonConfig

logger = logging.getLogger(__name__)

CONFIG_PATHS = [
    str(Path(__file__).parent / "settings.toml"),
    f"/etc/{APP_NAME}/settings.toml",
    expanduser(f"~/.config/{APP_NAME}/settings.toml"),
]


class ConfigRepository(BaseModel):
    """
    Configuration repository for the application.

    This class holds the application configuration and provides methods to load
    environment variables into the configuration.
    """

    common: CommonConfig = Field(default_factory=CommonConfig)  # Common configuration instance

    @classmethod
    def create(
        cls, options: dict[str, Any] | None = None, paths: list[str] = CONFIG_PATHS
    ) -> "ConfigRepository":
        """Factory method to create an instance of AppConfig with default values."""
        if options is None:
            options = {}

        etc_options = load_config_files(paths=paths)
        env_options = load_env_vars()
        fixed_options = deep_update(etc_options, env_options)
        fixed_options = deep_update(fixed_options, options)

        return cls(**fixed_options)

    def create_injector_builder(self) -> Callable[[Binder], None]:
        """
        Create an injector builder for dependency injection.

        Returns:
            Callable[[Binder], None]: Function to configure the injector.
        """

        def configure(binder: Binder) -> None:
            binder.bind(ConfigRepository, to=self)
            binder.bind(CommonConfig, to=self.common)

        return configure


def load_config_files(paths: list[str]) -> dict[str, Any]:
    """
    Load configuration from YAML files in the user's config directories.

    Returns:
        dict[str, Any]: Merged configuration data from all found files.
    """
    config_paths = [Path(path) for path in paths]

    config_data: dict[str, Any] = {}
    for path in config_paths:
        if path.exists():
            try:
                with open(path, "rb") as f:
                    data: dict[str, Any] = tomli.load(f) or {}
                    config_data.update(data)
            except Exception as e:
                logger.warning(f"Failed to load configuration file {path}: {e}")

    return config_data


def load_env_vars() -> dict[str, Any]:
    """
    Load environment variables with ENV_PREFIX.

    Supports both flat and nested configuration with arbitrary depth:
    - HOGEHOGE_COMMON__JOBS=16 -> common.jobs
    - HOGEHOGE_FANTIA__DOWNLOAD_THUMB=true -> fantia.download_thumb
    - HOGEHOGE_TEMP__HOGEHOGE__EXAMPLE=false -> temp.hogehoge.example

    Returns:
        dict[str, Any]: Configuration data from environment variables.
    """
    import os

    config_data: dict[str, Any] = {}

    for key, value in os.environ.items():
        if not key.startswith(ENV_PREFIX):
            continue

        # Remove the prefix and convert to lowercase
        setting_key = key[len(ENV_PREFIX) :].lower()

        # Handle nested fields (e.g., FANTIA__DOWNLOAD_THUMB -> fantia.download_thumb)
        if "__" in setting_key:
            parts = setting_key.split("__")

            # Navigate/create nested structure
            current_dict = config_data
            for part in parts[:-1]:  # All parts except the last one
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]

            # Set the final value
            current_dict[parts[-1]] = value
        else:
            # Handle top-level fields
            config_data[setting_key] = value

    return config_data
