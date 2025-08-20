"""Configuration module for the application."""

import logging
import os
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

DEFAULT_CONFIG_PATH = str(Path(__file__).parent / "settings.toml")
CONFIG_PATHS = [
    DEFAULT_CONFIG_PATH,
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
    def create(cls, *, options: dict[str, Any] | None = None) -> "ConfigRepository":
        """Factory method to create an instance of AppConfig with default values."""
        repo = cls.create_optional(options=options)
        if repo:
            return repo
        logger.error("Using default configuration.")
        repo = cls.create_optional(paths=[DEFAULT_CONFIG_PATH])
        if not repo:
            raise ValueError("Failed to create ConfigRepository")
        return repo

    @classmethod
    def create_optional(
        cls, *, options: dict[str, Any] | None = None, paths: list[str] | None = None
    ) -> "ConfigRepository | None":
        """Factory method to create an instance of AppConfig with default values."""
        if options is None:
            options = {}

        paths = paths or create_config_paths()

        try:
            etc_options = load_config_files(paths)
            env_options = load_env_vars()
            fixed_options = deep_update(etc_options, env_options)
            fixed_options = deep_update(fixed_options, options)
            return cls(**fixed_options)

        except Exception as e:
            logger.error(f"Failed to create ConfigRepository: {e}")
            return None

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


def create_config_paths() -> list[str]:
    """
    Create a list of configuration paths.

    Returns:
        list[str]: List of configuration file paths.
    """
    config_paths = os.environ.get(f"{ENV_PREFIX}CONFIG_PATHS", "").split(":")

    if config_paths != [""]:
        return [DEFAULT_CONFIG_PATH, *config_paths]

    return CONFIG_PATHS


def load_config_files(paths: list[str]) -> dict[str, Any]:
    """
    Load configuration from TOML files in the user's config directories.

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
