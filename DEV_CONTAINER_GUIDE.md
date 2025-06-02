# Dev Container セットアップガイド

## 🍎 Apple Silicon Mac 対応 Dev Container（完全版）

このプロジェクトはApple Silicon Mac（M1/M2/M3）での開発を完全サポートするDev Container環境を提供します。

## 🚀 クイックスタート

### 1. 前提条件

- **Docker Desktop**: Apple Silicon対応版をインストール
  ```bash
  # Homebrewでインストール
  brew install --cask docker
  ```

- **VS Code/Cursor + Dev Containers拡張**:
  ```bash
  # VS Codeインストール
  brew install --cask visual-studio-code
  
  # Dev Containers拡張をインストール
  code --install-extension ms-vscode-remote.remote-containers
  ```

### 2. 開発環境起動（推奨手順）

```bash
# 1. VS Code/Cursorでプロジェクトを開く
code /projects/shared/shift-scheduler

# 2. Command Palette (Cmd+Shift+P) を開いて実行:
# "Dev Containers: Rebuild Container"
```

### 3. 開発開始

Dev Container内で以下のコマンドが使用可能：

```bash
# 依存関係インストール
make setup

# アプリケーション起動
make run
# → http://localhost:8081 でアクセス

# テスト実行
make test

# コードフォーマット
make format
```

## 🎯 主要機能

### ✅ **Apple Silicon完全対応**
- ARM64ネイティブコンテナ
- Java 17 ARM64版
- マルチプラットフォームビルド対応

### ✅ **開発ツール統合**
- Python 3.11 + uv（高速パッケージマネージャー）
- Timefold Solver（Java 17）
- FastAPI + Uvicorn
- 自動コードフォーマット（Black, isort）

### ✅ **VS Code/Cursor拡張**
- Python開発サポート
- Docker管理
- Testing統合
- Linting（black, isort, flake8, mypy）
- デバッグサポート

## 🛠 トラブルシューティング

### 🔧 一般的な問題と解決方法

#### 1. **uv sync エラー**
```bash
# 問題: uv.lockファイルの破損
# 解決方法:
rm -f uv.lock
uv sync --no-install-project
```

#### 2. **Java環境エラー**
```bash
# Java環境確認
java -version
echo $JAVA_HOME

# 期待値: 
# OpenJDK 17
# JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
```

#### 3. **ポート8000が使用できない**
```bash
# ポート8081を使用（既に設定済み）
make run
# → http://localhost:8081 でアクセス
```

#### 4. **ブラウザアクセスできない**
```bash
# VS Code/CursorのPORTSタブを確認
# localhost:8081の🌐アイコンをクリック
# または右クリック → "Open in Browser"
```

#### 5. **bash history エラー**
```bash
# 解決方法:
mkdir -p /home/vscode/commandhistory
touch /home/vscode/commandhistory/.bash_history

# または Dev Container を完全リビルド
# Command Palette → "Dev Containers: Rebuild Container"
```

### 🔍 環境確認コマンド

```bash
# 全体確認
make check

# 個別確認
python --version    # Python 3.11.x
uv --version       # uv 0.7.x
java -version      # OpenJDK 17
echo $JAVA_HOME    # Java環境変数

# アプリケーション動作確認
curl http://localhost:8081/
curl http://localhost:8081/test  # Timefoldライブラリテスト
```

### 🆘 完全リセット手順

問題が解決しない場合の最終手段：

```bash
# 1. Docker環境のクリーンアップ
docker system prune -a

# 2. Dev Container完全リビルド
# VS Code/Cursor Command Palette:
# "Dev Containers: Rebuild Container"

# 3. 手動確認
cd /workspace
make setup
make run
```

## 📁 プロジェクト構成

```
shift-scheduler/
├── .devcontainer/
│   ├── devcontainer.json    # Dev Container設定
│   └── Dockerfile          # コンテナ定義
├── .vscode/                # VS Code設定
├── main.py                 # FastAPIアプリケーション
├── models.py               # データモデル
├── constraints.py          # Timefold制約定義
├── pyproject.toml          # Python依存関係
├── Makefile               # 開発コマンド
└── README.md              # プロジェクト説明
```

## 🚀 API エンドポイント

アプリケーション起動後、以下のエンドポイントが利用可能：

```bash
# 基本エンドポイント
GET  /                     # API情報
GET  /health              # ヘルスチェック
GET  /docs                # API仕様書

# シフトスケジューラー
GET  /api/shifts/demo     # デモデータ取得
POST /api/shifts/solve    # シフト最適化（非同期）
POST /api/shifts/solve-sync # シフト最適化（同期）
```

## 🎯 開発ワークフロー

### 1. **新機能開発**
```bash
# 依存関係追加
uv add package-name

# 開発
# (コードを編集)

# テスト
make test

# フォーマット（保存時自動実行）
make format
```

### 2. **API テスト**
```bash
# サーバー起動
make run

# 新しいターミナルでテスト
curl http://localhost:8081/api/shifts/demo
```

### 3. **デバッグ**
- VS Code/Cursorのデバッグ機能を使用
- ブレークポイント設定可能
- 変数の監視・ステップ実行対応

## 💡 ベストプラクティス

### **コード品質**
- 保存時自動フォーマット（Black, isort）
- Linting（flake8, mypy）
- 型ヒント推奨

### **テスト**
```bash
# 単体テスト
make test

# カバレッジ確認
uv run pytest --cov=.
```

### **パフォーマンス**
- Docker Desktop推奨設定: CPU 4コア以上、Memory 8GB以上
- ファイル同期最適化済み

## 📚 参考資料

- [Timefold Solver Documentation](https://docs.timefold.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [uv Documentation](https://github.com/astral-sh/uv)
- [Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)

## ✅ 成功確認チェックリスト

- [ ] Dev Container起動成功
- [ ] `make run` でサーバー起動
- [ ] http://localhost:8081 にブラウザアクセス可能
- [ ] `/test` エンドポイントでTimefoldライブラリ動作確認
- [ ] `/api/shifts/demo` でデモデータ取得可能
- [ ] VS Code/Cursorでデバッグ・テスト実行可能

## 🤝 サポート

問題が解決しない場合は、以下の情報をお教えください：
- macOSバージョン
- Docker Desktopバージョン
- VS Code/Cursorバージョン
- 具体的なエラーメッセージ
- `make check` の実行結果

---

**🎉 Happy Coding with Shift Scheduler!**
