"""CLI Application"""

from logging import getLogger

import click

from mcbot.cli._utils import click_verbose_option, config_logging
from mcbot.config.settings import ConfigRepository

logger = getLogger(__name__)


@click.command()
@click_verbose_option
def run(verbose: tuple[bool]) -> None:
    """Run the mcbot CLI application."""
    config = ConfigRepository.create()
    config_logging(config, verbose)

    logger.info("Starting mcbot CLI application...")
    print("Hello from mcbot!")  # noqa: T201
