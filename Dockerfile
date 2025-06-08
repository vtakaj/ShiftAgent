# Production Dockerfile (Multi-platform support)
FROM --platform=$BUILDPLATFORM python:3.11-slim as builder

# Build arguments
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies (production only)
RUN uv sync --frozen --no-dev

# ===== Runtime stage =====
FROM --platform=$TARGETPLATFORM python:3.11-slim

# Build arguments
ARG TARGETPLATFORM

# Update system packages and install Java and fonts (platform-specific)
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    curl \
    # WeasyPrint dependencies
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    # Japanese fonts
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME (platform-specific)
RUN if [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
    echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64' >> /etc/environment; \
    else \
    echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> /etc/environment; \
    fi

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY main.py models.py constraints.py ./

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Platform-specific JAVA_HOME setting
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port 8000
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]