"""Configuration management commands."""

import sys
from pathlib import Path

import click
import tomli_w

from mcbot.cli._utils import AliasedGroup, click_verbose_option, config_logging
from mcbot.config.settings import ConfigRepository, create_config_paths


@click.group(cls=AliasedGroup)
def config() -> None:
    """Configuration management commands."""


@config.command()
def show() -> None:
    """Show current configuration."""
    repo = ConfigRepository.create()

    click.echo("Current configuration:")
    click.echo(repo.model_dump_json(indent=2))


@config.command()
@click.option(
    "--path",
    type=click.Path(),
    default="./settings.toml",
    help="Path to generate the configuration file (default: ./settings.toml)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing configuration file",
)
@click_verbose_option
def init(path: str, force: bool, verbose: tuple[bool, ...]) -> None:
    """Generate a default configuration file."""
    repo = ConfigRepository.create()
    config_logging(repo, verbose)

    config_path = Path(path)
    if config_path.exists() and not force:
        click.echo(f"Configuration file already exists: {config_path}")
        click.echo("Use --force to overwrite.")
        sys.exit(1)

    default_config = repo.model_dump(exclude_unset=True)

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write configuration file
    with open(config_path, "wb") as f:
        tomli_w.dump(default_config, f)

    click.echo(f"Generated default configuration file: {config_path}")


@config.command()
@click.option(
    "--config-file",
    type=click.Path(exists=True),
    help="Path to configuration file to validate",
)
@click_verbose_option
def validate(config_file: str | None, verbose: tuple[bool, ...]) -> None:
    """Validate configuration file or current configuration."""
    repo = ConfigRepository.create()
    config_logging(repo, verbose)

    if config_file:
        repo_opt = ConfigRepository.create_optional(paths=[config_file])
        if repo_opt is None:
            click.echo("Configuration file is invalid.")
            raise click.Abort()

        click.echo("Configuration file is valid.")
        return

    repo_opt = ConfigRepository.create_optional()
    if repo_opt is None:
        click.echo("Current configuration is invalid.")
        raise click.Abort()

    click.echo("Current configuration is valid.")
    return


@config.command()
@click_verbose_option
def paths(verbose: tuple[bool, ...]) -> None:
    """Show configuration file search paths."""
    repo = ConfigRepository.create()
    config_logging(repo, verbose)

    click.echo("Configuration files are searched in the following order:")
    for i, path in enumerate(create_config_paths(), 1):
        click.echo(f"{i}. {path}")
