# Docker Buildx設定（Apple Silicon対応）
#!/bin/bash

set -e

echo "🍎 Apple Silicon Mac用 Docker環境セットアップ"

# Docker Buildxの確認とセットアップ
setup_buildx() {
    echo "🔧 Docker Buildxをセットアップ中..."
    
    # Buildxが利用可能か確認
    if ! docker buildx version > /dev/null 2>&1; then
        echo "❌ Docker Buildxが利用できません。Docker Desktopを最新版に更新してください。"
        exit 1
    fi
    
    # マルチプラットフォームビルダーの作成
    if ! docker buildx inspect multiplatform > /dev/null 2>&1; then
        echo "📱 マルチプラットフォームビルダーを作成中..."
        docker buildx create --name multiplatform --platform linux/amd64,linux/arm64
    fi
    
    # ビルダーの使用開始
    docker buildx use multiplatform
    
    echo "✅ Docker Buildxセットアップ完了"
}

# プラットフォーム検出
detect_platform() {
    echo "🔍 プラットフォームを検出中..."
    
    ARCH=$(uname -m)
    case $ARCH in
        arm64|aarch64)
            echo "✅ Apple Silicon (ARM64) detected"
            PLATFORM="linux/arm64"
            ;;
        x86_64|amd64)
            echo "ℹ️ Intel/AMD (x86_64) detected"
            PLATFORM="linux/amd64"
            ;;
        *)
            echo "⚠️ Unknown architecture: $ARCH"
            PLATFORM="linux/amd64"
            ;;
    esac
    
    echo "Platform: $PLATFORM"
}

# Dev Containerのビルド
build_dev_container() {
    echo "🐳 Dev Containerをビルド中..."
    
    cd .devcontainer
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --file Dockerfile \
        --tag shift-scheduler-dev:latest \
        --load \
        ..
    cd ..
    
    echo "✅ Dev Containerビルド完了"
}

# 本番用コンテナのビルド
build_production_container() {
    echo "🚀 本番用コンテナをビルド中..."
    
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --file Dockerfile \
        --tag shift-scheduler:latest \
        --tag shift-scheduler:$(date +%Y%m%d) \
        --load \
        .
    
    echo "✅ 本番用コンテナビルド完了"
}

# Docker環境の確認
check_docker_environment() {
    echo "🔍 Docker環境を確認中..."
    
    # Docker Desktopの起動確認
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Dockerが起動していません。Docker Desktopを起動してください。"
        exit 1
    fi
    
    # Docker Composeの確認
    if ! docker compose version > /dev/null 2>&1; then
        echo "❌ Docker Composeが利用できません。"
        exit 1
    fi
    
    echo "Docker version: $(docker --version)"
    echo "Docker Compose version: $(docker compose version)"
    echo "✅ Docker環境確認完了"
}

# メイン処理
main() {
    echo "🎯 Shift Scheduler Docker環境セットアップ開始"
    echo "=================================================="
    
    detect_platform
    check_docker_environment
    setup_buildx
    
    case "${1:-all}" in
        "dev")
            build_dev_container
            ;;
        "prod")
            build_production_container
            ;;
        "all")
            build_dev_container
            build_production_container
            ;;
        *)
            echo "Usage: $0 [dev|prod|all]"
            echo "  dev  - Dev Containerのみビルド"
            echo "  prod - 本番用コンテナのみビルド"
            echo "  all  - 両方ビルド（デフォルト）"
            exit 1
            ;;
    esac
    
    echo ""
    echo "🎉 セットアップ完了！"
    echo "次のコマンドでDev Containerを起動できます："
    echo "  make dev-up"
    echo "  code . (その後 'Dev Containers: Reopen in Container')"
}

# スクリプト実行
main "$@"