"""Pytest fixtures for tests."""

import pytest

from mcbot.modules.common import CommonConfig


@pytest.fixture(scope="function")
def common_config(tmp_path_factory: pytest.TempPathFactory) -> CommonConfig:
    """CommonConfigのテスト用fixture."""
    return CommonConfig(
        logging_config={},
        user_data_dir=str(tmp_path_factory.mktemp("user_data")),
        user_cache_dir=str(tmp_path_factory.mktemp("user_cache")),
        working_dir=str(tmp_path_factory.mktemp("working")),
    )
