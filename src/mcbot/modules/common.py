"""Common utilities for the modules."""

from typing import Any

from platformdirs import PlatformDirs
from pydantic import BaseModel, Field

from mcbot.env import APP_AUTHOR, APP_NAME

pfd = PlatformDirs(appname=APP_NAME, appauthor=APP_AUTHOR)


class CommonConfig(BaseModel):
    """
    Common configuration class for the application.

    This class holds global settings that can be accessed throughout the application.
    """

    logging_config: dict[str, Any] = Field(default_factory=dict)  # Logging configuration
    user_data_dir: str = Field(default=pfd.user_data_dir)  # User data directory
    user_cache_dir: str = Field(default=pfd.user_cache_dir)  # User cache directory
    working_dir: str = Field(default=".")  # Working directory
