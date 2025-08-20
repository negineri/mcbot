"""Tests for mcbot.cli._utils module."""

from pathlib import Path
from unittest.mock import Mock, patch

import click
import pytest

from mcbot.cli._utils import AliasedGroup, config_logging
from mcbot.config.settings import ConfigRepository


class TestAliasedGroup:
    @pytest.fixture
    def aliased_group(self) -> AliasedGroup:
        """Create AliasedGroup with test commands."""
        group = AliasedGroup()

        @group.command("start")
        def start_cmd() -> None:
            """Start command."""
            pass

        @group.command("stop")
        def stop_cmd() -> None:
            """Stop command."""
            pass

        return group

    @pytest.fixture
    def mock_ctx(self) -> Mock:
        """Create mock click Context."""
        ctx = Mock(spec=click.Context)
        ctx.fail = Mock(side_effect=lambda msg: (_ for _ in ()).throw(click.ClickException(msg)))
        ctx.token_normalize_func = None
        ctx.resilient_parsing = False
        return ctx

    def test_get_command_exact_match(self, aliased_group: AliasedGroup, mock_ctx: Mock) -> None:
        """Test getting command with exact name match."""
        cmd = aliased_group.get_command(mock_ctx, "start")
        assert cmd is not None
        assert cmd.name == "start"

    def test_get_command_prefix_match(self, aliased_group: AliasedGroup, mock_ctx: Mock) -> None:
        """Test prefix matching behavior: unique match works, ambiguous raises error."""
        # Test unique prefix match

        cmd = aliased_group.get_command(mock_ctx, "sta")  # Only matches start
        assert cmd is not None
        assert cmd.name == "start"

        with pytest.raises(click.ClickException):
            aliased_group.get_command(mock_ctx, "st")  # Matches both start and stop

    def test_get_command_no_match(self, aliased_group: AliasedGroup, mock_ctx: Mock) -> None:
        """Test getting command with no matches."""
        cmd = aliased_group.get_command(mock_ctx, "nonexistent")
        assert cmd is None

    def test_resolve_command_success(self, aliased_group: AliasedGroup, mock_ctx: Mock) -> None:
        """Test successful command resolution."""
        cmd_name, cmd, args = aliased_group.resolve_command(mock_ctx, ["start", "arg1"])
        assert cmd_name == "start"
        assert cmd is not None
        assert args == ["arg1"]  # args contains only remaining arguments

    @pytest.mark.parametrize("command", [["st", "arg1"], ["nonexistent", "arg1"]])
    def test_resolve_command_failures(
        self, aliased_group: AliasedGroup, mock_ctx: Mock, command: list[str]
    ) -> None:
        """Test command resolution failure cases."""
        with pytest.raises(click.ClickException):
            aliased_group.resolve_command(mock_ctx, command)

    def test_resolve_command_custom_badparameter(self, mock_ctx: Mock) -> None:
        """Test custom BadParameter is raised when cmd.name is None."""
        group = AliasedGroup()

        # Mock the parent resolve_command to return a command with None name
        mock_cmd = Mock()
        mock_cmd.name = None

        with patch.object(click.Group, "resolve_command", return_value=("test", mock_cmd, ["arg"])):
            with pytest.raises(click.BadParameter, match="Command 'arg' not found"):
                group.resolve_command(mock_ctx, ["arg"])


class TestConfigLogging:
    @pytest.fixture
    def mock_config(self, tmp_path: Path) -> ConfigRepository:
        """Create mock ConfigRepository."""
        config = ConfigRepository()
        config.common.user_data_dir = str(tmp_path)
        config.common.logging_config = {
            "version": 1,
            "handlers": {
                "console": {"level": "WARNING"},
                "file": {"filename": "%(user_data_dir)s/logs/app.log"},
            },
        }
        return config

    @pytest.fixture
    def mock_config_no_file(self) -> ConfigRepository:
        """Create mock ConfigRepository without file handler."""
        config = ConfigRepository()
        config.common.logging_config = {"version": 1, "handlers": {"console": {"level": "WARNING"}}}
        return config

    @patch("mcbot.cli._utils.dictConfig")
    def test_config_logging_default(
        self, mock_dict_config: Mock, mock_config_no_file: ConfigRepository
    ) -> None:
        """Test default logging configuration."""
        config_logging(mock_config_no_file)

        mock_dict_config.assert_called_once_with(mock_config_no_file.common.logging_config)

    @patch("mcbot.cli._utils.dictConfig")
    @patch("mcbot.cli._utils.logger")
    def test_config_logging_verbose_single(
        self, mock_logger: Mock, mock_dict_config: Mock, mock_config_no_file: ConfigRepository
    ) -> None:
        """Test logging configuration with single verbose flag."""
        config_logging(mock_config_no_file, verbose=(True,))

        assert mock_config_no_file.common.logging_config["handlers"]["console"]["level"] == "INFO"
        mock_dict_config.assert_called_once_with(mock_config_no_file.common.logging_config)
        mock_logger.info.assert_called_once_with("Setting log level to INFO")

    @patch("mcbot.cli._utils.dictConfig")
    @patch("mcbot.cli._utils.logger")
    def test_config_logging_verbose_multiple(
        self, mock_logger: Mock, mock_dict_config: Mock, mock_config_no_file: ConfigRepository
    ) -> None:
        """Test logging configuration with multiple verbose flags."""
        config_logging(mock_config_no_file, verbose=(True, True))

        assert mock_config_no_file.common.logging_config["handlers"]["console"]["level"] == "DEBUG"
        mock_dict_config.assert_called_once_with(mock_config_no_file.common.logging_config)
        mock_logger.info.assert_called_once_with("Setting log level to DEBUG")

    @patch("mcbot.cli._utils.dictConfig")
    def test_config_logging_with_file_handler(
        self, mock_dict_config: Mock, mock_config: ConfigRepository
    ) -> None:
        """Test logging configuration with file handler creates directory."""
        log_dir = Path(mock_config.common.user_data_dir) / "logs"
        log_file_path = log_dir / "app.log"

        config_logging(mock_config)

        # Check that %(user_data_dir)s was replaced
        assert mock_config.common.logging_config["handlers"]["file"]["filename"] == str(
            log_file_path
        )
        assert log_dir.exists()  # Ensure directory was created
        # Check that dictConfig was called
        mock_dict_config.assert_called_once_with(mock_config.common.logging_config)

    @patch("mcbot.cli._utils.dictConfig")
    def test_config_logging_verbose_empty_tuple(
        self, mock_dict_config: Mock, mock_config_no_file: ConfigRepository
    ) -> None:
        """Test logging configuration with empty verbose tuple."""
        config_logging(mock_config_no_file, verbose=())

        mock_dict_config.assert_called_once_with(mock_config_no_file.common.logging_config)

    @patch("mcbot.cli._utils.dictConfig")
    @patch("mcbot.cli._utils.logger")
    def test_config_logging_file_handler_with_verbose(
        self,
        mock_logger: Mock,
        mock_dict_config: Mock,
        mock_config: ConfigRepository,
    ) -> None:
        """Test logging configuration with file handler and verbose flag."""
        expected_path = Path(mock_config.common.user_data_dir) / "logs" / "app.log"

        config_logging(mock_config, verbose=(True,))

        assert mock_config.common.logging_config["handlers"]["file"]["filename"] == str(
            expected_path
        )
        # Check verbose logging configuration
        assert mock_config.common.logging_config["handlers"]["console"]["level"] == "INFO"
        mock_dict_config.assert_called_once_with(mock_config.common.logging_config)
        mock_logger.info.assert_called_once_with("Setting log level to INFO")
