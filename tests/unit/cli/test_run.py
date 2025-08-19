"""Unit tests for the CLI module."""

from unittest.mock import patch

from click.testing import CliRunner

from mcbot.cli.run import run


class TestRun:
    """mcbot runコマンドのテスト"""

    def setup_method(self) -> None:
        self.runner = CliRunner()
        patch("mcbot.cli.run.ConfigRepository").start()
        patch("mcbot.cli.run.config_logging").start()

    def test_run_command(self) -> None:
        result = self.runner.invoke(run, [])
        assert result.exit_code == 0
        assert "Hello from mcbot!" in result.output
