"""Entry point for the CLI."""

import click

from mcbot.cli._utils import AliasedGroup, config_logging
from mcbot.cli.config import config
from mcbot.cli.run import run
from mcbot.config.settings import ConfigRepository


@click.group(cls=AliasedGroup)
@click.version_option()
def main() -> None:
    """Entry point for the CLI."""
    repo = ConfigRepository.create()

    # Configure logging
    config_logging(repo)


main.add_command(run)
main.add_command(config)
