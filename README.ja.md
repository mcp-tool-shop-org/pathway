<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/pathway/readme.png" alt="Pathway logo" width="400">
</p>

<p align="center">
    <em>Append-only journey engine where undo never erases learning.</em>
</p>

<p align="center">
    <a href="https://github.com/mcp-tool-shop-org/pathway/actions/workflows/ci.yml">
        <img src="https://github.com/mcp-tool-shop-org/pathway/actions/workflows/ci.yml/badge.svg" alt="CI">
    </a>
    <a href="https://pypi.org/project/mcpt-pathway/">
        <img src="https://img.shields.io/pypi/v/mcpt-pathway" alt="PyPI version">
    </a>
    <a href="https://opensource.org/licenses/MIT">
        <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
    </a>
    <a href="https://mcp-tool-shop-org.github.io/pathway/">
        <img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page">
    </a>
</p>

**Pathway Coreは、追記のみを行う学習エンジンであり、アンドゥ操作によって学習内容が消えることはありません。**

アンドゥはナビゲーションです。学習内容は保持されます。

## 哲学

従来の「アンドゥ」機能は、履歴を書き換えます。Pathwayは書き換えません。

Pathwayでアンドゥ操作を行うと、元のパスが残ったまま、過去への参照を持つ新しいイベントが作成されます。失敗したパスで何かを学んだ場合、その知識は保持されます。間違いは消えるのではなく、学習の機会となります。

これにより、Pathwayは実際に何が起こったのかを正確に反映します。

## 機能

- **追記のみのイベントログ**: イベントは編集または削除されません。
- **アンドゥ = ポインタの移動**: アンドゥ操作は、新しいイベントを作成し、ヘッドを移動させます。
- **学習内容の保持**: 学習内容は、アンドゥ操作やブランチを越えて保持されます。
- **ブランチ機能**: Gitのような、アンドゥ操作後に新しい作業を行う際の、暗黙的な分岐機能があります。

## クイックスタート

```bash
# Install
pip install -e ".[dev]"

# Initialize database
python -m pathway.cli init

# Import sample session
python -m pathway.cli import sample_session.jsonl

# View derived state
python -m pathway.cli state sess_001

# Start API server
python -m pathway.cli serve
```

## APIエンドポイント

- `POST /events` - イベントの追加
- `GET /session/{id}/state` - 派生した状態の取得 (JourneyView, LearnedView, ArtifactView)
- `GET /session/{id}/events` - 生のイベントの取得
- `GET /sessions` - すべてのセッションのリスト表示
- `GET /event/{id}` - 単一のイベントの取得

## イベントタイプ

学習プロセス全体をカバーする14種類のイベントタイプがあります。

| Type | 目的 |
| ------ | --------- |
| IntentCreated | ユーザーの目標とコンテキスト |
| TrailVersionCreated | 学習パス/マップ |
| WaypointEntered | パス上でのナビゲーション |
| ChoiceMade | ユーザーが分岐を選択 |
| StepCompleted | ユーザーが特定のタスクを完了 |
| Blocked | ユーザーが問題に遭遇 |
| Backtracked | ユーザーがアンドゥ操作 |
| Replanned | パスが修正 |
| マージ | ブランチが統合 |
| ArtifactCreated | 生成された成果物 |
| ArtifactSuperseded | 古い成果物が置き換え |
| PreferenceLearned | ユーザーの学習スタイル |
| ConceptLearned | ユーザーが理解した内容 |
| ConstraintLearned | ユーザーの環境に関する情報 |

## 派生ビュー

システムは、イベントから以下の3つのビューを生成します。

1. **JourneyView**: 現在の場所、ブランチ、訪問済みのポイント
2. **LearnedView**: 信頼度スコア付きのユーザーの好み、概念、制約
3. **ArtifactView**: すべての成果物と、その置き換え履歴

## セキュリティ

- **APIキー**: `PATHWAY_API_KEY`環境変数を設定して、書き込みエンドポイントを保護します。
- **ペイロード制限**: デフォルトは1MB ( `PATHWAY_MAX_PAYLOAD_SIZE`で設定可能)
- **セッションIDの検証**: 英数字、アンダースコア、ハイフンのみ、最大128文字

## テスト

```bash
pytest  # 73 tests covering invariants, API, reducers, store
```

## アーキテクチャ

```
pathway/
├── models/         # Pydantic models for events and views
├── store/          # SQLite event store + JSONL import/export
├── reducers/       # Compute derived views from events
├── api/            # FastAPI endpoints
└── cli.py          # Command-line tools
```
