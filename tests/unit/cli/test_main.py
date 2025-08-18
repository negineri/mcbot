"""Unit tests for the CLI module."""

from click.testing import CliRunner

from mcbot.cli.main import main


class TestMain:
    """mcbot コマンドのテスト"""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_main_command(self) -> None:
        result = self.runner.invoke(main, [])
        assert result.exit_code == 2
        assert "Entry point for the CLI." in result.output

    def test_main_command_with_help(self) -> None:
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_main_command_with_version(self) -> None:
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output
