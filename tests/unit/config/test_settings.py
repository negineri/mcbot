"""Tests for mcbot.config.settings module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from injector import Binder

from mcbot.config.settings import (
    CONFIG_PATHS,
    ConfigRepository,
    load_config_files,
    load_env_vars,
)
from mcbot.modules.common import CommonConfig


class TestConfigRepository:
    def test_init_default(self) -> None:
        """Test ConfigRepository initialization with default values."""
        config = ConfigRepository()

        assert isinstance(config.common, CommonConfig)
        assert config.common.logging_config == {}
        assert config.common.working_dir == "."

    def test_init_with_common_config(self) -> None:
        """Test ConfigRepository initialization with custom CommonConfig."""
        common_config = CommonConfig(
            logging_config={"version": 1, "handlers": {}}, working_dir="/custom/dir"
        )
        config = ConfigRepository(common=common_config)

        assert config.common == common_config
        assert config.common.logging_config == {"version": 1, "handlers": {}}
        assert config.common.working_dir == "/custom/dir"

    @patch("mcbot.config.settings.load_config_files")
    @patch("mcbot.config.settings.load_env_vars")
    def test_create_default(self, mock_load_env: Mock, mock_load_files: Mock) -> None:
        """Test ConfigRepository.create with default parameters."""
        mock_load_files.return_value = {"common": {"working_dir": "test_dir"}}
        mock_load_env.return_value = {"common": {"logging_config": {"level": "INFO"}}}

        config = ConfigRepository.create()

        mock_load_files.assert_called_once_with(paths=CONFIG_PATHS)
        mock_load_env.assert_called_once()

        assert config.common.working_dir == "test_dir"
        assert config.common.logging_config == {"level": "INFO"}

    @patch("mcbot.config.settings.load_config_files")
    @patch("mcbot.config.settings.load_env_vars")
    def test_create_with_options(self, mock_load_env: Mock, mock_load_files: Mock) -> None:
        """Test ConfigRepository.create with custom options."""
        mock_load_files.return_value = {"common": {"working_dir": "file_dir"}}
        mock_load_env.return_value = {"common": {"working_dir": "env_dir"}}
        options = {"common": {"working_dir": "option_dir"}}

        config = ConfigRepository.create(options=options)

        # Options should override env which overrides files
        assert config.common.working_dir == "option_dir"

    @patch("mcbot.config.settings.load_config_files")
    @patch("mcbot.config.settings.load_env_vars")
    def test_create_with_custom_paths(self, mock_load_env: Mock, mock_load_files: Mock) -> None:
        """Test ConfigRepository.create with custom config paths."""
        mock_load_files.return_value = {}
        mock_load_env.return_value = {}
        custom_paths = ["/custom/path1", "/custom/path2"]

        ConfigRepository.create(paths=custom_paths)

        mock_load_files.assert_called_once_with(paths=custom_paths)

    def test_create_injector_builder(self) -> None:
        """Test create_injector_builder returns correct configuration function."""
        config = ConfigRepository()
        mock_binder = Mock(spec=Binder)

        configure_fn = config.create_injector_builder()
        configure_fn(mock_binder)

        # Check that both ConfigRepository and CommonConfig are bound
        expected_calls = [
            ((ConfigRepository,), {"to": config}),
            ((CommonConfig,), {"to": config.common}),
        ]

        actual_calls = [(call[0], call[1]) for call in mock_binder.bind.call_args_list]
        assert actual_calls == expected_calls


class TestLoadConfigFiles:
    def test_load_config_files_empty_list(self) -> None:
        """Test load_config_files with empty path list."""
        result = load_config_files([])
        assert result == {}

    def test_load_config_files_nonexistent_paths(self) -> None:
        """Test load_config_files with nonexistent paths."""
        result = load_config_files(["/nonexistent1.toml", "/nonexistent2.toml"])
        assert result == {}

    def test_load_config_files_valid_file(self) -> None:
        """Test load_config_files with valid TOML file."""
        toml_content = """
        [common]
        working_dir = "test_dir"

        [common.logging_config]
        version = 1
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            temp_path = f.name

        try:
            result = load_config_files([temp_path])

            assert "common" in result
            assert result["common"]["working_dir"] == "test_dir"
            assert result["common"]["logging_config"]["version"] == 1
        finally:
            Path(temp_path).unlink()

    def test_load_config_files_multiple_files(self) -> None:
        """Test load_config_files with multiple TOML files."""
        file1_content = """
        [common]
        working_dir = "dir1"
        user_data_dir = "data1"
        """

        file2_content = """
        [common]
        working_dir = "dir2"  # This should override file1's common section
        user_cache_dir = "cache2"

        [other_section]
        value = "other"
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f1:
            f1.write(file1_content)
            path1 = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f2:
            f2.write(file2_content)
            path2 = f2.name

        try:
            result = load_config_files([path1, path2])

            # file2 completely replaces file1's [common] section due to dict.update()
            assert result["common"]["working_dir"] == "dir2"
            assert result["common"]["user_cache_dir"] == "cache2"
            # user_data_dir from file1 is lost due to section replacement
            assert "user_data_dir" not in result["common"]

            # New section from file2
            assert result["other_section"]["value"] == "other"
        finally:
            Path(path1).unlink()
            Path(path2).unlink()

    @patch("mcbot.config.settings.logger")
    def test_load_config_files_invalid_toml(self, mock_logger: Mock) -> None:
        """Test load_config_files with invalid TOML content."""
        invalid_toml = "invalid toml [[ content"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(invalid_toml)
            temp_path = f.name

        try:
            result = load_config_files([temp_path])

            assert result == {}
            mock_logger.warning.assert_called_once()
            assert "Failed to load configuration file" in mock_logger.warning.call_args[0][0]
        finally:
            Path(temp_path).unlink()

    @patch("builtins.open", side_effect=PermissionError("Access denied"))
    @patch("mcbot.config.settings.logger")
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_config_files_permission_error(
        self, mock_exists: Mock, mock_logger: Mock, mock_open_fn: Mock
    ) -> None:
        """Test load_config_files handles permission errors gracefully."""
        test_path = "/restricted/config.toml"
        result = load_config_files([test_path])

        # Verify mocks were called
        mock_exists.assert_called()
        mock_open_fn.assert_called()

        assert result == {}
        mock_logger.warning.assert_called_once()
        assert "Failed to load configuration file" in mock_logger.warning.call_args[0][0]


class TestLoadEnvVars:
    def test_load_env_vars_empty(self) -> None:
        """Test load_env_vars with no matching environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            result = load_env_vars()
            assert result == {}

    @patch("mcbot.config.settings.ENV_PREFIX", "TEST_")
    def test_load_env_vars_simple(self) -> None:
        """Test load_env_vars with simple top-level variables."""
        env_vars = {
            "TEST_SIMPLE": "value1",
            "TEST_ANOTHER": "value2",
            "OTHER_VAR": "ignored",  # Different prefix
        }

        with patch.dict(os.environ, env_vars, clear=True):
            result = load_env_vars()

            assert result == {"simple": "value1", "another": "value2"}

    @patch("mcbot.config.settings.ENV_PREFIX", "TEST_")
    def test_load_env_vars_nested(self) -> None:
        """Test load_env_vars with nested configuration."""
        env_vars = {
            "TEST_COMMON__WORKING_DIR": "/test/dir",
            "TEST_COMMON__USER_DATA_DIR": "/test/data",
            "TEST_LOGGING__LEVEL": "DEBUG",
            "TEST_DEEP__NESTED__VALUE": "deep_value",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            result = load_env_vars()

            expected = {
                "common": {"working_dir": "/test/dir", "user_data_dir": "/test/data"},
                "logging": {"level": "DEBUG"},
                "deep": {"nested": {"value": "deep_value"}},
            }

            assert result == expected

    @patch("mcbot.config.settings.ENV_PREFIX", "TEST_")
    def test_load_env_vars_mixed(self) -> None:
        """Test load_env_vars with mixed simple and nested variables."""
        env_vars = {
            "TEST_SIMPLE_VAR": "simple",
            "TEST_NESTED__VALUE": "nested",
            "TEST_NESTED__ANOTHER": "another_nested",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            result = load_env_vars()

            expected = {
                "simple_var": "simple",
                "nested": {"value": "nested", "another": "another_nested"},
            }

            assert result == expected

    @patch("mcbot.config.settings.ENV_PREFIX", "TEST_")
    def test_load_env_vars_case_conversion(self) -> None:
        """Test load_env_vars converts keys to lowercase."""
        env_vars = {
            "TEST_UPPER_CASE": "value1",
            "TEST_MixedCase": "value2",
            "TEST_lower_case": "value3",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            result = load_env_vars()

            expected = {"upper_case": "value1", "mixedcase": "value2", "lower_case": "value3"}

            assert result == expected

    @patch("mcbot.config.settings.ENV_PREFIX", "TEST_")
    def test_load_env_vars_overwrites_nested(self) -> None:
        """Test load_env_vars handles overwriting nested structures."""
        env_vars = {
            "TEST_CONFIG__FIRST": "first_value",
            "TEST_CONFIG__SECOND": "second_value",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            result = load_env_vars()

            expected = {"config": {"first": "first_value", "second": "second_value"}}

            assert result == expected
