"""Unit tests for the CLI module."""

from collections.abc import Generator
from unittest.mock import patch

from click.testing import CliRunner
from pytest import fixture

from mcbot.cli.run import run


@fixture
def cli_runner() -> Generator[CliRunner, None, None]:
    with patch("mcbot.cli.run.ConfigRepository"), patch("mcbot.cli.run.config_logging"):
        yield CliRunner()


class TestRun:
    """mcbot runコマンドのテスト"""

    def test_run_command(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(run, [])
        assert result.exit_code == 0
        assert "Hello from mcbot!" in result.output
