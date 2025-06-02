# Shift Scheduler API

Timefold Solver を使った Shift Scheduler API です。

## 🚀 クイックスタート

### 前提条件

```bash
# Docker Desktop
brew install --cask docker

# VS Code + Dev Containers拡張
brew install --cask visual-studio-code
code --install-extension ms-vscode-remote.remote-containers
```

### 開発環境起動

**方法1: VS Code Dev Container（推奨）**
```bash
# プロジェクトを開く
code /projects/shared/shift-scheduler

# Command Palette (Cmd+Shift+P) → "Dev Containers: Reopen in Container"
```

**方法2: セットアップスクリプト**
```bash
cd /projects/shared/shift-scheduler

# Docker環境セットアップ
chmod +x setup-docker.sh
./setup-docker.sh

# Dev Container起動
make dev-setup
```

### 開発開始

Dev Container内で：
```bash
# 依存関係インストール
make setup

# アプリケーション起動
make run  # → http://localhost:8081

# テスト実行
make test

# API仕様確認
# → http://localhost:8081/docs (Swagger UI)
```

## 📁 プロジェクト構造

```
shift-scheduler/
├── .devcontainer/          # Dev Container設定
│   ├── devcontainer.json   # VS Code Dev Container設定
│   ├── docker-compose.yml  # Dev Container用Docker Compose
│   └── Dockerfile          # Dev Container用Dockerfile
├── .vscode/                # VS Code設定
│   ├── settings.json       # エディター設定
│   ├── launch.json         # デバッグ設定
│   └── extensions.json     # 推奨拡張機能
├── main.py                 # FastAPI メインアプリケーション
├── models.py               # Timefold Solver データモデル
├── constraints.py          # シフト最適化制約定義
├── api-test.http           # REST Client APIテスト
├── Dockerfile              # 本番用Dockerfile（マルチプラットフォーム）
├── docker-compose.yml      # 本番用Docker Compose
├── pyproject.toml          # uv設定ファイル
├── Makefile                # 開発効率化コマンド
└── README.md               # このファイル
```

## 🎯 主要機能

### ✅ **シフト最適化**
- **スキルベース割り当て**: 必要スキルと従業員スキルのマッチング
- **時間制約管理**: シフト重複防止、最低休憩時間確保
- **週勤務時間制約**: 40時間制限、最小勤務時間、目標時間調整
- **公平性最適化**: 労働時間の均等分配

## 📊 API仕様

### 基本エンドポイント

```http
GET  /health                    # ヘルスチェック
GET  /api/shifts/demo          # デモデータ
POST /api/shifts/solve-sync    # 同期シフト最適化
POST /api/shifts/solve         # 非同期シフト最適化
GET  /api/shifts/solve/{id}    # 最適化結果取得
POST /api/shifts/analyze-weekly # 週勤務時間分析
```

### リクエスト例

```json
{
  "employees": [
    {
      "id": "emp1",
      "name": "田中太郎",
      "skills": ["看護師", "CPR", "フルタイム"]
    }
  ],
  "shifts": [
    {
      "id": "morning_shift",
      "start_time": "2025-06-01T08:00:00",
      "end_time": "2025-06-01T16:00:00",
      "required_skills": ["看護師"],
      "location": "病院",
      "priority": 1
    }
  ]
}
```

## 🔧 制約システム

| レベル | 制約名 | 説明 |
|--------|--------|------|
| **HARD** | スキルマッチング | 必要スキルを持つ従業員のみ割り当て |
| **HARD** | シフト重複防止 | 同一従業員の同時間帯重複禁止 |
| **HARD** | 週最大勤務時間 | 45時間超過で制約違反 |
| **MEDIUM** | 最低休憩時間 | 連続シフト間8時間休憩 |
| **MEDIUM** | 週最小勤務時間 | フルタイム32時間以上 |
| **SOFT** | 労働時間公平分配 | 従業員間の勤務時間格差最小化 |
| **SOFT** | 週勤務時間目標 | 個人目標時間への近似 |

## 🧪 テスト・デバッグ

### VS Code統合テスト
```bash
# テストエクスプローラーでの実行
# Command Palette → "Test: Run All Tests"

# デバッグ実行
# F5キー → "FastAPI Server" 設定でデバッグ開始
```

### REST Clientテスト
```bash
# api-test.httpファイルを開いて
# APIリクエストの上の "Send Request" をクリック
```

### コマンドラインテスト
```bash
make test-api      # API動作確認
make test-solve    # シフト最適化テスト
make test          # フルテストスイート
```

## 🛠 トラブルシューティング

### プラットフォーム確認
```bash
make check-platform        # 現在のプラットフォーム情報
make troubleshoot          # 包括的なトラブルシューティング
```

### よくある問題

**Java関連エラー**
```bash
# Dev Container内でJAVA_HOME確認
echo $JAVA_HOME
# 期待値: /usr/lib/jvm/java-17-openjdk
```

**uv関連エラー**
```bash
# uvの再インストール
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

**Dev Containerビルドエラー**
```bash
# キャッシュクリアして再ビルド
make dev-rebuild
```

## 🚀 本番デプロイ

### マルチプラットフォームビルド
```bash
# マルチプラットフォーム対応
make build-multi-platform

# プラットフォーム指定ビルド
docker buildx build --platform linux/arm64 -t shift-scheduler:arm64 .
docker buildx build --platform linux/amd64 -t shift-scheduler:amd64 .
```

### Docker Compose本番起動
```bash
# 本番環境用
docker-compose -f docker-compose.yml up -d
```

## 🔄 開発ワークフロー

1. **VS CodeでDev Container起動**
2. **コード編集** (自動フォーマット・リント)
3. **ブレークポイントでデバッグ**
4. **REST Clientでテスト**
5. **Git commit** (自動テスト実行)

## 📚 参考資料

- [Timefold Solver Documentation](https://docs.timefold.ai/)
- [uv Package Manager](https://github.com/astral-sh/uv)
- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)

## 🤝 コントリビューション

1. Dev Containerで開発環境起動
2. フィーチャーブランチ作成: `git checkout -b feature/new-feature`
3. 変更とテスト: `make test && make lint`
4. コミット: `git commit -am 'Add new feature'`
5. プッシュ: `git push origin feature/new-feature`
6. Pull Request作成

---

# API動作テスト
test-api:
	@echo "🌐 API動作テスト:"
	@echo "ヘルスチェック:"
	curl -s http://localhost:8081/health | jq . || curl -s http://localhost:8081/health
	@echo "\nデモデータ取得:"
	curl -s http://localhost:8081/api/shifts/demo | jq '.statistics' || echo "サーバーが起動していません"

# デバッグモード
debug:
	@echo "🐛 デバッグモードで起動..."
	uv run uvicorn main:app --host 0.0.0.0 --port 8081 --reload --log-level debug
