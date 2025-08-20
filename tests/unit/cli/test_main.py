"""Unit tests for the CLI module."""

from collections.abc import Generator

from click.testing import CliRunner
from pytest import fixture

from mcbot.cli.main import main


@fixture
def cli_runner() -> Generator[CliRunner, None, None]:
    yield CliRunner()


class TestMain:
    """mcbot コマンドのテスト"""

    def test_main_command(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(main, [])
        assert result.exit_code == 2
        assert "Entry point for the CLI." in result.output

    def test_main_command_with_help(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_main_command_with_version(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output
