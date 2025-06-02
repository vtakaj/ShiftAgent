# Dev Container Makefile（修正版）
.PHONY: help setup install dev run test format lint clean

# デフォルトターゲット
help:
	@echo "🚀 Shift Scheduler Dev Container コマンド:"
	@echo ""
	@echo "  setup        - 開発環境セットアップ（初回実行推奨）"
	@echo "  install      - 依存関係のみインストール"
	@echo "  dev          - 開発用依存関係インストール"
	@echo "  run          - FastAPIサーバー起動"
	@echo "  test         - テスト実行"
	@echo "  format       - コードフォーマット"
	@echo "  lint         - コードチェック"
	@echo "  clean        - キャッシュクリア"

# 開発環境セットアップ（エラー処理付き）
setup:
	@echo "🔧 開発環境をセットアップ中..."
	@rm -f uv.lock
	@echo "📦 依存関係をインストール中..."
	uv sync --no-install-project
	@echo "✅ セットアップ完了！"

# 依存関係のインストール
install:
	@echo "📦 依存関係をインストール中..."
	uv sync --no-install-project

# 開発用依存関係のインストール
dev:
	@echo "🛠 開発用依存関係をインストール中..."
	uv sync --all-extras

# FastAPIサーバー起動
run:
	@echo "🚀 FastAPIサーバーを起動中..."
	@echo "サーバーURL: http://localhost:8081"
	@echo "API仕様: http://localhost:8081/docs"
	uv run uvicorn main:app --host 0.0.0.0 --port 8081 --reload

# テスト実行
test:
	@echo "🧪 テストを実行中..."
	uv run pytest -v

# コードフォーマット
format:
	@echo "✨ コードをフォーマット中..."
	uv run black .
	uv run isort .

# コードチェック
lint:
	@echo "🔍 コードをチェック中..."
	uv run flake8 . || true
	uv run mypy . || true

# キャッシュクリア
clean:
	@echo "🧹 キャッシュをクリア中..."
	uv cache clean
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# 環境確認
check:
	@echo "🔍 環境を確認中..."
	@echo "Python: $(shell python --version 2>&1 || echo 'Not found')"
	@echo "uv: $(shell uv --version 2>&1 || echo 'Not found')"
	@echo "Java: $(shell java -version 2>&1 | head -1 || echo 'Not found')"
	@echo "JAVA_HOME: $(JAVA_HOME)"
	@echo "Current directory: $(shell pwd)"
	@echo "Files: $(shell ls -la | head -5)"

# API動作テスト
test-api:
	@echo "🌐 API動作テスト:"
	@echo "ヘルスチェック:"
	curl -s http://localhost:8000/health | jq . || curl -s http://localhost:8000/health
	@echo "\nデモデータ取得:"
	curl -s http://localhost:8000/api/shifts/demo | jq '.statistics' || echo "サーバーが起動していません"

# トラブルシューティング
troubleshoot:
	@echo "🔧 トラブルシューティング情報:"
	@$(MAKE) check
	@echo ""
	@echo "uv環境:"
	uv show || echo "uv sync が必要かもしれません"
	@echo ""
	@echo "解決方法:"
	@echo "1. make setup を実行"
	@echo "2. エラーが続く場合は make clean && make setup"
	@echo "3. それでも問題がある場合は Dev Container を Rebuild"

# 簡単な開発フロー
dev-start: setup run

# デバッグモード
debug:
	@echo "🐛 デバッグモードで起動..."
	uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug