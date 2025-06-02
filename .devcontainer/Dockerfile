# Apple Silicon Mac対応 Dev Container Dockerfile
FROM python:3.11-slim

# Build arguments for multi-platform support
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Install system dependencies (Apple Silicon対応)
RUN apt-get update && apt-get install -y \
    # Java 17 (ARM64/AMD64両対応)
    openjdk-17-jdk \
    # 開発ツール
    git \
    curl \
    wget \
    build-essential \
    # その他のユーティリティ
    vim \
    nano \
    htop \
    jq \
    tree \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# JAVA_HOME設定（動的に検出）
RUN JAVA_HOME_PATH=$(find /usr/lib/jvm -name "java-17-openjdk*" | head -1) && \
    echo "export JAVA_HOME=$JAVA_HOME_PATH" >> /etc/environment && \
    echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> /etc/environment

# Non-root user for development
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME

# uvをインストール（Apple Silicon対応）
USER $USERNAME
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/$USERNAME/.local/bin:$PATH"

# Bash history persistence
RUN mkdir -p /home/$USERNAME/commandhistory && \
    touch /home/$USERNAME/commandhistory/.bash_history && \
    chown -R $USERNAME:$USERNAME /home/$USERNAME/commandhistory && \
    echo 'export PROMPT_COMMAND="history -a"' >> /home/$USERNAME/.bashrc && \
    echo 'export HISTFILE=/home/$USERNAME/commandhistory/.bash_history' >> /home/$USERNAME/.bashrc

# Git configuration for the container
RUN git config --global init.defaultBranch main && \
    git config --global core.autocrlf input

# Python environment setup
WORKDIR /workspace

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Java環境変数（実行時に設定されるように）
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Apple Silicon Macの場合のJAVA_HOME設定
RUN if [ "$(uname -m)" = "aarch64" ]; then \
        echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64' >> /home/$USERNAME/.bashrc; \
    else \
        echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> /home/$USERNAME/.bashrc; \
    fi

# uvのパス設定
RUN echo 'export PATH="/home/vscode/.local/bin:$PATH"' >> /home/$USERNAME/.bashrc

# 開発に便利なエイリアス設定
RUN echo 'alias ll="ls -la"' >> /home/$USERNAME/.bashrc && \
    echo 'alias serve="make run"' >> /home/$USERNAME/.bashrc && \
    echo 'alias test-all="make test"' >> /home/$USERNAME/.bashrc

CMD ["/bin/bash"]