"""Dependency injection container configuration."""

from injector import Binder, Injector

from mcbot.config.settings import ConfigRepository


def configure(binder: Binder) -> None:
    """Configure the dependency injection container."""


def create_injector(config: ConfigRepository) -> Injector:
    """Create a new injector instance.

    Args:
        config (ConfigRepository): Configuration repository.

    Returns:
        Injector: New injector instance.
    """
    return Injector([config.create_injector_builder(), configure])
