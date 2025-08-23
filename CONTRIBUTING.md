# 開発者向け コントリビューションガイド

MCBot プロジェクトへのコントリビューションをお考えいただき、ありがとうございます！

## 🚀 開発環境のセットアップ

### 必要な環境

- [uv](https://docs.astral.sh/uv/) (Python パッケージ管理)
- Git
- mise (推奨)

### 初回セットアップ

```bash
# 1. リポジトリをフォーク・クローン
git clone https://github.com/negineri/mcbot.git
cd mcbot

# 2. 依存関係をインストール
uv sync

# 3. Pre-commit フックをインストール
uv run pre-commit install
```

## 📋 開発ワークフロー

### 1. Issue の確認・作成

- 既存の Issue を確認し、重複がないかチェック
- 新機能・バグ修正の場合は Issue を作成してディスカッション
- Issue には以下を含める：
  - 問題の詳細な説明
  - 再現手順（バグの場合）
  - 期待される動作
  - 環境情報

### 2. ブランチの作成

```bash
# メインブランチから最新を取得
git checkout main
git pull origin main

# 機能ブランチを作成
git checkout -b feature/your-feature-name
# または
git checkout -b fix/issue-number-description
```

### 3. 開発・テスト

```bash
# テスト駆動開発を推奨
# 1. テストを先に書く
uv run pytest tests/unit/modules/your_module/test_your_file.py

# 2. 実装する

# 3. テストが通ることを確認
uv run pytest

# 4. 全体のテストを実行
uv run pytest
uv run mypy src
uv run ruff check src tests
uv run import-linter
```

### 4. コミット

```bash
# 変更をステージング
git add -A

# Conventional Commits 形式でコミット
git commit -m "feat: add new feature description"
git commit -m "fix: resolve issue with specific component"
git commit -m "docs: update contributing guide"
```

#### コミットメッセージの形式

```text
<type>: <description>

[optional body]

[optional footer]
```

**Type:**

- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント変更
- `style`: コードスタイルの変更（機能に影響なし）
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: その他の変更

### 5. プルリクエスト

```bash
# ブランチをプッシュ
git push origin feature/your-feature-name
```

GitHub でプルリクエストを作成する

## 🧪 テスト指針

### テスト分類と実行

```bash
# 単体テスト（高速、独立）
uv run pytest -m unit -n auto

# 統合テスト（モジュール間）
uv run pytest -m integration

# E2E テスト（全体ワークフロー）
uv run pytest -m e2e

# カバレッジ付きテスト
uv run pytest --cov=src/mcbot --cov-report=html
```

### テスト作成のガイドライン

テストコードは E2E テストと単体テストから構成されます。単体テストは/src とミラーリング構造にしてください。
単体テストはロンドン派です。他ライブラリの機能は Mock しなくてよいですが、プロジェクトの他ファイルで実装されている機能は Mock してください。

#### AAA パターン (Arrange, Act, Assert)

```python
def test_config_creation() -> None:
    # Arrange
    config_data = {"key": "value"}

    # Act
    config = create_config(config_data)

    # Assert
    assert config.key == "value"
```

#### テスト名は仕様を表現

```python
def test_should_raise_error_when_config_file_not_found() -> None:
    pass

def test_should_return_default_value_when_key_missing() -> None:
    pass
```

## 📝 コード品質基準

### コーディング規約

#### Python スタイル

- **PEP 8** 準拠（Ruff で自動チェック）
- **行の長さ**: 100 文字以内
- **型ヒント**: テストコードも含め、必須（MyPy strict モード）
- **Docstring**: Google スタイル or 1 行

```python
def process_data(input_data: dict[str, Any]) -> ProcessedResult:
    """データを処理する関数.

    Args:
        input_data: 処理対象のデータ辞書

    Returns:
        処理結果オブジェクト

    Raises:
        ValueError: 入力データが無効な場合
    """
    pass
```

### アーキテクチャルール

1. **レイヤー分離**

   - CLI → Config → Dependencies → Modules
   - 上位層は下位層に依存可能、逆は禁止

2. **モジュラーモノリス**

   - 異なるドメイン機能は`modules/your_module/`に分離する
   - module 内は Usecase → Infrastructure → Domain → Module Config
   - module は common module 以外の他の module を参照してはならない。
     - 複数のモジュールを連携させる Usecase は`scenario`に実装する。
   - ハードコードを避け、odule 固有の値は`modules/your_module/config.py`に纏める。

3. **依存性注入**

   - コンストラクタインジェクション優先
   - Domain から Infrastructure への依存が発生した場合、インターフェースによる依存性逆転を行う

### エラーハンドリング

- Exception は原則レイヤー内で解決し、上位レイヤーには失敗は None や空 list の返却でエラーを伝える
- エラーの詳細は logging を使って報告する

## 🔍 レビュープロセス

### レビュー観点

1. **機能性**

   - 要件を満たしているか
   - エッジケースが考慮されているか
   - エラーハンドリングが適切か

2. **品質**

   - コードの可読性・保守性
   - テストの網羅性
   - パフォーマンスへの影響

3. **アーキテクチャ**

   - 設計原則に従っているか
   - 依存関係が適切か
   - 拡張性が考慮されているか

### レビューコメントの例

```markdown
💡 提案: この処理は `utils.py` に共通関数として抽出できませんか？

❓ 質問: この例外処理は必要ですか？どんなケースを想定していますか？

🐛 バグ: `None` チェックが不足しているため、実行時エラーの可能性があります
```

### レビュー対応

- **建設的な議論**: 不明な点は積極的に質問
- **迅速な対応**: レビューコメントには 24 時間以内に返答
- **学習機会**: コードレビューは知識共有の場

## 🚀 リリースプロセス

### バージョニング

プロジェクトは [Semantic Versioning](https://semver.org/) に従います：

- **MAJOR**: 破壊的変更
- **MINOR**: 新機能追加（後方互換性あり）
- **PATCH**: バグ修正

### リリース手順

```bash
# 1. バージョンアップ
uv run bump-my-version bump patch  # または minor, major

# 2. タグプッシュ（自動実行）
git push orogin --tags
```
