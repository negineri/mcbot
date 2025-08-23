"""Tests for mcbot.config.settings module."""

import os
from pathlib import Path
from unittest.mock import patch

from injector import Injector
from pytest import LogCaptureFixture, MonkeyPatch

from mcbot.config.settings import (
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

    def test_init_with_common_config(self) -> None:
        """Test ConfigRepository initialization with custom CommonConfig."""
        common_config = CommonConfig(logging_config={"version": 1, "handlers": {}})
        config = ConfigRepository(common=common_config)

        assert config.common == common_config
        assert config.common.logging_config == {"version": 1, "handlers": {}}

    def test_create_default(self) -> None:
        """Test ConfigRepository.create with default parameters."""
        config = ConfigRepository.create()

        assert config is not None
        assert isinstance(config.common, CommonConfig)

    def test_create_with_valid_options(self) -> None:
        """Test ConfigRepository.create with valid options."""
        options = {"common": {"user_data_dir": "test_dir"}}  # Valid type
        config = ConfigRepository.create(options=options)

        assert config is not None
        assert config.common.user_data_dir == Path("test_dir")

    def test_create_with_invalid_options(self, caplog: LogCaptureFixture) -> None:
        """Test ConfigRepository.create with invalid options."""
        caplog.set_level("ERROR")
        options = {"common": {"user_data_dir": 123}}  # Invalid type
        config = ConfigRepository.create(options=options)

        assert config is not None
        assert "Failed to create ConfigRepository" in caplog.text

    def test_create_optional_with_options(self) -> None:
        """Test ConfigRepository.create with default parameters."""
        config = ConfigRepository.create_optional(options={"common": {"user_data_dir": "test_dir"}})

        assert config is not None
        assert config.common.user_data_dir == Path("test_dir")

    def test_create_optional_with_paths(self, tmp_path: Path) -> None:
        """Test ConfigRepository.create with optional paths."""
        config_path = tmp_path / "settings.toml"
        config_path.write_text(
            """
            [common]
            user_data_dir = "test_dir"
            """
        )
        config = ConfigRepository.create_optional(paths=[str(config_path)])

        assert config is not None
        assert config.common.user_data_dir == Path("test_dir")

    def test_create_injector_builder(self) -> None:
        """Test create_injector_builder returns correct configuration function."""
        config = ConfigRepository()

        configure_fn = config.create_injector_builder()
        injector = Injector([configure_fn])
        injected_config = injector.get(ConfigRepository)

        assert id(injected_config) == id(config)


class TestLoadConfigFiles:
    def test_load_config_files_empty_list(self) -> None:
        """Test load_config_files with empty path list."""
        result = load_config_files([])
        assert result == {}

    def test_load_config_files_nonexistent_paths(self) -> None:
        """Test load_config_files with nonexistent paths."""
        result = load_config_files(["/nonexistent1.toml", "/nonexistent2.toml"])
        assert result == {}

    def test_load_config_files_valid_file(self, tmp_path: Path) -> None:
        """Test load_config_files with valid TOML file."""
        toml_content = """
        [common]
        user_data_dir = "test_dir"

        [common.logging_config]
        version = 1
        """

        config_path = tmp_path / "settings.toml"
        config_path.write_text(toml_content)

        result = load_config_files([str(config_path)])

        assert "common" in result
        assert result["common"]["user_data_dir"] == "test_dir"
        assert result["common"]["logging_config"]["version"] == 1

    def test_load_config_files_multiple_files(self, tmp_path: Path) -> None:
        """Test load_config_files with multiple TOML files."""
        file1_content = """
        [common]
        user_data_dir = "data1"
        """

        file2_content = """
        [common]
        user_data_dir = "dir2"  # This should override file1's common section
        user_cache_dir = "cache2"

        [other_section]
        value = "other"
        """

        config_path1 = tmp_path / "settings1.toml"
        config_path1.write_text(file1_content)

        config_path2 = tmp_path / "settings2.toml"
        config_path2.write_text(file2_content)

        result = load_config_files([str(config_path1), str(config_path2)])

        # file2 completely replaces file1's [common] section due to dict.update()
        assert result["common"]["user_data_dir"] == "dir2"

        # file2 completely replaces file1's [common] section due to dict.update()
        assert result["common"]["user_cache_dir"] == "cache2"

        # New section from file2
        assert result["other_section"]["value"] == "other"

    def test_load_config_files_invalid_toml(
        self, caplog: LogCaptureFixture, tmp_path: Path
    ) -> None:
        """Test load_config_files with invalid TOML content."""
        invalid_toml = "invalid toml [[ content"
        config_path = tmp_path / "invalid_config.toml"
        config_path.write_text(invalid_toml)

        load_config_files([str(config_path)])

        assert "Failed to load configuration file" in caplog.text


class TestLoadEnvVars:
    def test_load_env_vars_empty(self) -> None:
        """Test load_env_vars with no matching environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            result = load_env_vars()
            assert result == {}

    def test_load_env_vars_simple(self, monkeypatch: MonkeyPatch) -> None:
        """Test load_env_vars with simple top-level variables."""
        monkeypatch.setenv("MCBOT_SIMPLE", "value1")
        monkeypatch.setenv("MCBOT_ANOTHER", "value2")
        monkeypatch.setenv("OTHER_VAR", "ignored")  # Different prefix

        result = load_env_vars()

        assert result["simple"] == "value1"
        assert result["another"] == "value2"
        assert "other_var" not in result  # Should be ignored

    def test_load_env_vars_nested(self, monkeypatch: MonkeyPatch) -> None:
        """Test load_env_vars with nested configuration."""
        monkeypatch.setenv("MCBOT_COMMON__USER_DATA_DIR", "/test/data")
        monkeypatch.setenv("MCBOT_LOGGING__LEVEL", "DEBUG")
        monkeypatch.setenv("MCBOT_DEEP__NESTED__VALUE", "deep_value")

        result = load_env_vars()

        assert result["common"]["user_data_dir"] == "/test/data"
        assert result["logging"]["level"] == "DEBUG"
        assert result["deep"]["nested"]["value"] == "deep_value"

    def test_load_env_vars_case_conversion(self, monkeypatch: MonkeyPatch) -> None:
        """Test load_env_vars converts keys to lowercase."""
        monkeypatch.setenv("MCBOT_UPPER_CASE", "value1")
        monkeypatch.setenv("MCBOT_MixedCase", "value2")
        monkeypatch.setenv("MCBOT_lower_case", "value3")

        result = load_env_vars()

        assert result["upper_case"] == "value1"
        assert result["mixedcase"] == "value2"
        assert result["lower_case"] == "value3"
