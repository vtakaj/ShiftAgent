# Dev Container Dockerfile for Apple Silicon Mac
FROM python:3.11-slim

# Build arguments for multi-platform support
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Install system dependencies (Apple Silicon support)
RUN apt-get update && apt-get install -y \
    # Java 17 (ARM64/AMD64 support)
    openjdk-17-jdk \
    # Development tools
    git \
    curl \
    wget \
    build-essential \
    unzip \
    # Other utilities
    vim \
    nano \
    htop \
    jq \
    tree \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# JAVA_HOME configuration (dynamic detection)
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

# Install uv (Apple Silicon support)
USER $USERNAME
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/$USERNAME/.local/bin:$PATH"

# Install Terraform CLI (Apple Silicon support)
USER root
RUN TERRAFORM_VERSION="1.8.0" && \
    ARCH=$(dpkg --print-architecture) && \
    curl -Lo /tmp/terraform.zip "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip" && \
    unzip /tmp/terraform.zip -d /tmp && \
    mv /tmp/terraform /usr/local/bin/ && \
    rm /tmp/terraform.zip && \
    terraform version
USER vscode

# Git configuration for the container
RUN git config --global init.defaultBranch main && \
    git config --global core.autocrlf input

# Python environment setup
WORKDIR /workspace

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Java environment variables (set at runtime)
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# JAVA_HOME configuration for Apple Silicon Mac
RUN if [ "$(uname -m)" = "aarch64" ]; then \
    echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64' >> /home/$USERNAME/.bashrc; \
    else \
    echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> /home/$USERNAME/.bashrc; \
    fi

# uv path configuration
RUN echo 'export PATH="/home/vscode/.local/bin:$PATH"' >> /home/$USERNAME/.bashrc

# Development aliases
RUN echo 'alias ll="ls -la"' >> /home/$USERNAME/.bashrc && \
    echo 'alias serve="make run"' >> /home/$USERNAME/.bashrc && \
    echo 'alias test-all="make test"' >> /home/$USERNAME/.bashrc

CMD ["/bin/bash"]
