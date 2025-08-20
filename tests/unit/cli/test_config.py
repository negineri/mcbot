"""Unit tests for the CLI config module."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner
from pytest import MonkeyPatch, fixture

from mcbot.cli.config import config, init, paths, show, validate


@fixture(autouse=True)
def mock_dependencies() -> Generator[None, None, None]:
    with (
        patch("mcbot.cli.config.ConfigRepository"),
        patch("mcbot.cli.config.config_logging"),
    ):
        yield None


class TestConfig:
    """config コマンドのテスト"""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    def test_config_group(self) -> None:
        """config コマンドグループのテスト"""
        result = self.runner.invoke(config, [])
        assert result.exit_code == 2
        assert "Configuration management commands." in result.output


class TestShow:
    """config show コマンドのテスト"""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    @patch("mcbot.cli.config.ConfigRepository")
    def test_show_command(self, mock_config_repo: MagicMock) -> None:
        """show コマンドのテスト"""
        mock_repo = MagicMock()
        mock_repo.model_dump_json.return_value = '{"key": "value"}'
        mock_config_repo.create.return_value = mock_repo

        result = self.runner.invoke(show, [])

        assert result.exit_code == 0
        assert "Current configuration:" in result.output
        assert '{"key": "value"}' in result.output
        mock_config_repo.create.assert_called_once()
        mock_repo.model_dump_json.assert_called_once_with(indent=2)


class TestInit:
    """config init コマンドのテスト"""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    @patch("mcbot.cli.config.ConfigRepository")
    def test_init_command_custom_path(
        self,
        mock_config_repo: MagicMock,
        tmp_path: Path,
    ) -> None:
        """init コマンドのカスタムパステスト"""
        mock_repo = MagicMock()
        mock_repo.model_dump.return_value = {"test": "config"}
        mock_config_repo.create.return_value = mock_repo
        config_file = tmp_path / "settings.toml"

        result = self.runner.invoke(init, ["--path", str(config_file)])

        assert result.exit_code == 0
        assert "Generated default configuration file:" in result.output
        assert config_file.exists()

    def test_init_command_file_exists_without_force(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """init コマンドのファイル存在時テスト（force なし）"""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "settings.toml"
        config_file.touch()

        result = self.runner.invoke(init, [])

        assert result.exit_code == 1
        assert "Configuration file already exists: settings.toml" in result.output
        assert "Use --force to overwrite." in result.output

    def test_init_command_file_exists_with_force(
        self,
        monkeypatch: MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """init コマンドのファイル存在時テスト（force あり）"""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "settings.toml"
        config_file.touch()

        result = self.runner.invoke(init, ["--force"])

        assert result.exit_code == 0
        assert "Generated default configuration file: settings.toml" in result.output


class TestValidate:
    """config validate コマンドのテスト"""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    @patch("mcbot.cli.config.ConfigRepository")
    def test_validate_command_current_config_valid(
        self,
        mock_config_repo: MagicMock,
    ) -> None:
        """validate コマンドの現在設定有効テスト"""
        mock_repo = MagicMock()
        mock_config_repo.create.return_value = mock_repo

        result = self.runner.invoke(validate, [])

        assert result.exit_code == 0
        assert "Current configuration is valid." in result.output
        mock_config_repo.create.assert_called_with()

    @patch("mcbot.cli.config.ConfigRepository")
    def test_validate_command_current_config_invalid(
        self,
        mock_config_repo: MagicMock,
    ) -> None:
        """validate コマンドの現在設定無効テスト"""
        mock_config_repo.create_optional.return_value = None

        result = self.runner.invoke(validate, [])

        assert result.exit_code == 1
        assert "Current configuration is invalid." in result.output

    @patch("mcbot.cli.config.ConfigRepository")
    def test_validate_command_specific_config_valid(
        self,
        mock_config_repo: MagicMock,
        tmp_path: Path,
    ) -> None:
        """validate コマンドの特定設定ファイル有効テスト"""
        mock_repo = MagicMock()
        mock_config_repo.create_optional.return_value = mock_repo
        config_path = tmp_path / "test_config.toml"
        config_path.touch()

        result = self.runner.invoke(validate, ["--config-file", str(config_path)])

        assert result.exit_code == 0
        assert "Configuration file is valid." in result.output
        mock_config_repo.create_optional.assert_called_once_with(paths=[str(config_path)])

    @patch("mcbot.cli.config.ConfigRepository")
    def test_validate_command_specific_config_invalid(
        self,
        mock_config_repo: MagicMock,
        tmp_path: Path,
    ) -> None:
        """validate コマンドの特定設定ファイル無効テスト"""
        mock_config_repo.create_optional.return_value = None

        config_path = tmp_path / "test_config.toml"
        config_path.touch()

        result = self.runner.invoke(validate, ["--config-file", str(config_path)])

        assert result.exit_code == 1
        assert "Configuration file is invalid." in result.output


class TestPaths:
    """config paths コマンドのテスト"""

    def setup_method(self) -> None:
        self.runner = CliRunner()

    @patch("mcbot.cli.config.create_config_paths")
    def test_paths_command(self, mock_create_config_paths: MagicMock) -> None:
        """paths コマンドのテスト"""
        mock_create_config_paths.return_value = ["/path1/config.toml", "/path2/config.toml"]

        result = self.runner.invoke(paths, [])

        assert result.exit_code == 0
        assert "Configuration files are searched in the following order:" in result.output
        assert "1. /path1/config.toml" in result.output
        assert "2. /path2/config.toml" in result.output
