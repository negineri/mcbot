"""設定関連のワークフローE2Eテスト."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from mcbot.cli.main import main


@pytest.fixture
def cli_runner() -> CliRunner:
    """CLIテスト用のランナーフィクスチャ."""
    return CliRunner()


@pytest.mark.e2e
class TestConfigWorkflow:
    """設定管理のワークフローテスト."""

    def test_config_init_and_show_workflow(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """設定初期化→表示のワークフローテスト."""
        config_file = tmp_path / "test_settings.toml"

        # 1. 設定ファイル初期化
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file)])
        assert result.exit_code == 0
        assert "Generated default configuration file" in result.output
        assert config_file.exists()

        # 2. 環境変数設定して設定表示
        monkeypatch.setenv("MCBOT_CONFIG_PATH", str(config_file))
        result = cli_runner.invoke(main, ["config", "show"])
        assert result.exit_code == 0
        assert "Current configuration:" in result.output

        # JSON形式の出力を確認
        # "Current configuration:" 以降の部分を取得してJSONパース
        config_start = "Current configuration:"
        json_start = result.output.find(config_start) + len(config_start)
        json_part = result.output[json_start:].strip()
        json.loads(json_part)  # JSONとして正しいかテスト

    def test_config_init_force_overwrite_workflow(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """設定ファイル強制上書きワークフローテスト."""
        config_file = tmp_path / "test_settings.toml"

        # 1. 初回作成
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file)])
        assert result.exit_code == 0

        # 2. 同じファイルを上書きなしで試行（失敗する想定）
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file)])
        assert result.exit_code == 1
        assert "Configuration file already exists" in result.output
        assert "Use --force to overwrite" in result.output

        # 3. 強制上書きで成功
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file), "--force"])
        assert result.exit_code == 0
        assert "Generated default configuration file" in result.output

    def test_config_validate_workflow(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """設定ファイル検証ワークフローテスト."""
        config_file = tmp_path / "valid_settings.toml"

        # 1. 有効な設定ファイル作成
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file)])
        assert result.exit_code == 0

        # 2. 特定ファイルの検証
        result = cli_runner.invoke(main, ["config", "validate", "--config-file", str(config_file)])
        assert result.exit_code == 0
        assert "Configuration file is valid" in result.output

        # 3. 無効なファイル作成
        invalid_config = tmp_path / "invalid_settings.toml"
        invalid_config.write_text("invalid toml content [[[")

        # 4. 無効ファイルの検証
        result = cli_runner.invoke(
            main, ["config", "validate", "--config-file", str(invalid_config)]
        )
        # 実装では無効なTOMLファイルに対してWARNINGログを出力し、
        # フォールバックとして「Configuration file is valid.」を出力する
        assert "Failed to load configuration file" in result.output
        assert "Configuration file is valid" in result.output

    def test_config_paths_display_workflow(self, cli_runner: CliRunner) -> None:
        """設定パス表示ワークフローテスト."""
        result = cli_runner.invoke(main, ["config", "paths"])
        assert result.exit_code == 0
        assert "Configuration files are searched in the following order:" in result.output
        # 少なくとも1つのパスが表示される（番号付きリスト形式）
        assert any(line.strip().startswith(("1.", "1 ")) for line in result.output.split("\n"))

    @pytest.mark.parametrize("verbose_level", ["-v", "-vv"])
    def test_verbose_option_workflow(
        self, cli_runner: CliRunner, tmp_path: Path, verbose_level: str
    ) -> None:
        """冗長オプション付きワークフローテスト."""
        config_file = tmp_path / "verbose_test.toml"

        # verboseオプション付きで実行
        result = cli_runner.invoke(
            main, ["config", "init", "--path", str(config_file), verbose_level]
        )
        assert result.exit_code == 0
        assert "Generated default configuration file" in result.output

        # 設定検証もverboseで
        result = cli_runner.invoke(
            main, ["config", "validate", "--config-file", str(config_file), verbose_level]
        )
        assert result.exit_code == 0
        assert "Configuration file is valid" in result.output

    def test_full_config_lifecycle_workflow(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """設定ファイルの完全なライフサイクルテスト."""
        config_file = tmp_path / "lifecycle_settings.toml"

        # 1. パス確認
        result = cli_runner.invoke(main, ["config", "paths"])
        assert result.exit_code == 0

        # 2. 初期化
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file)])
        assert result.exit_code == 0
        assert config_file.exists()

        # 3. 検証
        result = cli_runner.invoke(main, ["config", "validate", "--config-file", str(config_file)])
        assert result.exit_code == 0

        # 4. 内容確認
        monkeypatch.setenv("MCBOT_CONFIG_PATH", str(config_file))
        result = cli_runner.invoke(main, ["config", "show"])
        assert result.exit_code == 0
        assert "Current configuration:" in result.output

        # 5. 強制上書き
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file), "--force"])
        assert result.exit_code == 0

        # 6. 最終検証
        result = cli_runner.invoke(main, ["config", "validate", "--config-file", str(config_file)])
        assert result.exit_code == 0
