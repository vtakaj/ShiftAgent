# 本番用Dockerfile（マルチプラットフォーム対応）
FROM --platform=$BUILDPLATFORM python:3.11-slim as builder

# Build arguments
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# uvをインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 作業ディレクトリ設定
WORKDIR /app

# プロジェクトファイルをコピー
COPY pyproject.toml uv.lock ./

# 依存関係をインストール（本番用のみ）
RUN uv sync --frozen --no-dev

# ===== 実行ステージ =====
FROM --platform=$TARGETPLATFORM python:3.11-slim

# Build arguments
ARG TARGETPLATFORM

# システムパッケージの更新とJavaのインストール（プラットフォーム対応）
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    curl \
    && rm -rf /var/lib/apt/lists/*

# JAVA_HOME設定（プラットフォーム別）
RUN if [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
        echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64' >> /etc/environment; \
    else \
        echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> /etc/environment; \
    fi

# 作業ディレクトリ設定
WORKDIR /app

# ビルドステージから仮想環境をコピー
COPY --from=builder /app/.venv /app/.venv

# PATH環境変数に仮想環境を追加
ENV PATH="/app/.venv/bin:$PATH"

# アプリケーションコードをコピー
COPY main.py models.py constraints.py ./

# 非rootユーザーを作成
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# プラットフォーム別のJAVA_HOME設定
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ポート8000を公開
EXPOSE 8000

# アプリケーションの実行
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]