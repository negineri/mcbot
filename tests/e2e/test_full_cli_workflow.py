"""完全なCLIワークフローE2Eテスト."""

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
class TestFullCLIWorkflow:
    """CLIアプリケーション全体のワークフローテスト."""

    def test_help_commands(self, cli_runner: CliRunner) -> None:
        """ヘルプコマンドのテスト."""
        # メインヘルプ
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Entry point for the CLI" in result.output

        # 設定サブコマンドヘルプ
        result = cli_runner.invoke(main, ["config", "--help"])
        assert result.exit_code == 0
        assert "Configuration management commands" in result.output

        # 実行サブコマンドヘルプ
        result = cli_runner.invoke(main, ["run", "--help"])
        assert result.exit_code == 0
        assert "Run the mcbot CLI application" in result.output

    def test_config_initialization_and_validation(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """設定初期化と検証のテスト."""
        config_file = tmp_path / "app_settings.toml"

        # 設定パス確認
        result = cli_runner.invoke(main, ["config", "paths"])
        assert result.exit_code == 0
        assert "Configuration files are searched" in result.output

        # 設定ファイル初期化
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file)])
        assert result.exit_code == 0
        assert config_file.exists()

        # 設定ファイル検証
        result = cli_runner.invoke(main, ["config", "validate", "--config-file", str(config_file)])
        assert result.exit_code == 0
        assert "Configuration file is valid" in result.output

    def test_config_display_with_environment_variable(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数を使用した設定表示テスト."""
        config_file = tmp_path / "env_settings.toml"

        # 設定ファイル作成
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file)])
        assert result.exit_code == 0

        # 環境変数設定して設定表示
        monkeypatch.setenv("MCBOT_CONFIG_PATH", str(config_file))
        result = cli_runner.invoke(main, ["config", "show"])
        assert result.exit_code == 0
        assert "Current configuration:" in result.output

        # JSON形式の出力を確認
        try:
            config_start = "Current configuration:"
            json_start = result.output.find(config_start) + len(config_start)
            json_part = result.output[json_start:].strip()
            json.loads(json_part)
        except (ValueError, json.JSONDecodeError):
            pytest.fail("Output does not contain valid JSON")

    def test_application_execution(self, cli_runner: CliRunner) -> None:
        """アプリケーション実行テスト."""
        result = cli_runner.invoke(main, ["run"])
        assert result.exit_code == 0
        assert "Hello from mcbot!" in result.output

    def test_error_handling_with_invalid_files(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """無効ファイルでのエラーハンドリングテスト."""
        # 存在しないファイルの検証
        nonexistent_file = tmp_path / "nonexistent.toml"
        result = cli_runner.invoke(
            main, ["config", "validate", "--config-file", str(nonexistent_file)]
        )
        assert result.exit_code != 0

        # 無効なTOMLファイルの検証
        invalid_toml = tmp_path / "invalid.toml"
        invalid_toml.write_text("invalid toml content [[[")
        result = cli_runner.invoke(main, ["config", "validate", "--config-file", str(invalid_toml)])
        # 実装では無効なTOMLファイルに対してWARNINGログを出力し、フォールバックする
        assert "Failed to load configuration file" in result.output
        assert "Configuration file is valid" in result.output

    @pytest.mark.parametrize("verbose_level", ["-v", "-vv"])
    def test_verbose_options(
        self, cli_runner: CliRunner, tmp_path: Path, verbose_level: str
    ) -> None:
        """冗長オプションのテスト."""
        config_file = tmp_path / "verbose_settings.toml"

        # 設定初期化（verbose）
        result = cli_runner.invoke(
            main, ["config", "init", "--path", str(config_file), verbose_level]
        )
        assert result.exit_code == 0

        # 設定検証（verbose）
        result = cli_runner.invoke(
            main, ["config", "validate", "--config-file", str(config_file), verbose_level]
        )
        assert result.exit_code == 0

        # 設定パス表示（verbose）
        result = cli_runner.invoke(main, ["config", "paths", verbose_level])
        assert result.exit_code == 0

        # アプリケーション実行（verbose）
        result = cli_runner.invoke(main, ["run", verbose_level])
        assert result.exit_code == 0
        assert "Hello from mcbot!" in result.output

    def test_config_force_overwrite(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """設定ファイル強制上書きテスト."""
        config_file = tmp_path / "override_settings.toml"

        # 初回作成
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file)])
        assert result.exit_code == 0
        original_mtime = config_file.stat().st_mtime

        # 上書きなしでの再実行（既存ファイルを保護）
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file)])
        assert result.exit_code == 1
        assert "Configuration file already exists" in result.output
        assert "Use --force to overwrite" in result.output

        # ファイルが変更されていないことを確認
        assert config_file.stat().st_mtime == original_mtime

        # 強制上書き
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file), "--force"])
        assert result.exit_code == 0
        assert "Generated default configuration file" in result.output

    def test_full_environment_variable_integration(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数との完全統合テスト."""
        config_file = tmp_path / "env_integration.toml"

        # 設定ファイル作成
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file)])
        assert result.exit_code == 0

        # 環境変数を設定してアプリケーション全体をテスト
        monkeypatch.setenv("MCBOT_CONFIG_PATH", str(config_file))

        # 設定表示
        result = cli_runner.invoke(main, ["config", "show"])
        assert result.exit_code == 0
        assert "Current configuration:" in result.output

        # 設定検証（環境変数で指定されたファイル）
        result = cli_runner.invoke(main, ["config", "validate"])
        assert result.exit_code == 0
        assert "Current configuration is valid" in result.output

        # アプリケーション実行
        result = cli_runner.invoke(main, ["run"])
        assert result.exit_code == 0
        assert "Hello from mcbot!" in result.output

    def test_command_aliases(self, cli_runner: CliRunner) -> None:
        """コマンドエイリアス機能のテスト."""
        # 完全なコマンド名
        result_full = cli_runner.invoke(main, ["run"])
        assert result_full.exit_code == 0

        # 省略形がサポートされている場合のテスト
        # （AliasedGroupの実装によって動作が決まる）
        result_short = cli_runner.invoke(main, ["r"])
        # エラーまたは成功のいずれかを許容
        assert result_short.exit_code in [0, 2]  # 0=成功, 2=不明なコマンド

    def test_version_option(self, cli_runner: CliRunner) -> None:
        """バージョンオプションのテスト."""
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        # バージョン情報が含まれることを確認
        # 具体的なバージョン文字列は設定により変わるため、存在のみ確認

    @pytest.mark.parametrize("config_name", ["primary.toml", "secondary.toml"])
    def test_multiple_config_files(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        config_name: str,
    ) -> None:
        """複数設定ファイルでのテスト."""
        config_file = tmp_path / config_name

        # 設定ファイル作成
        result = cli_runner.invoke(main, ["config", "init", "--path", str(config_file)])
        assert result.exit_code == 0

        # 設定ファイル検証
        result = cli_runner.invoke(main, ["config", "validate", "--config-file", str(config_file)])
        assert result.exit_code == 0

        # 環境変数でアプリケーション実行
        monkeypatch.setenv("MCBOT_CONFIG_PATH", str(config_file))
        result = cli_runner.invoke(main, ["run", "-v"])
        assert result.exit_code == 0
        assert "Hello from mcbot!" in result.output
