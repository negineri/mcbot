"""Dependency injection container configuration."""

from injector import Binder, Injector

from mcbot.config.settings import ConfigRepository


def configure(binder: Binder) -> None:
    """Configure the dependency injection container."""


def get_injector() -> Injector:
    """Get configured injector instance.

    Returns:
        Configured injector instance.
    """
    config = ConfigRepository.create()
    return Injector([config.create_injector_builder(), configure])
