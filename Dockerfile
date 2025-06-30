# Default Dockerfile for CI/CD - API service
# This is a symlink-like reference to the actual API Dockerfile

# ==== Build Stage ====
FROM python:3.11-slim AS builder

# Build arguments
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN chmod +x /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (production only, no dev dependencies)
RUN /bin/uv sync --frozen --no-dev --no-install-project

# ==== Runtime Stage ====
FROM python:3.11-slim AS runtime

# Build arguments
ARG TARGETPLATFORM

# Install system dependencies including Java 17 for Timefold Solver
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set JAVA_HOME dynamically based on platform
RUN JAVA_HOME_PATH=$(find /usr/lib/jvm -name "java-17-openjdk-*" -type d | head -1) && \
    echo "export JAVA_HOME=$JAVA_HOME_PATH" >> /etc/environment && \
    echo "JAVA_HOME=$JAVA_HOME_PATH" >> /etc/environment

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source code
COPY src/ ./src/

# Create non-root user for security and set up directories
RUN useradd --create-home --shell /bin/bash --uid 1000 app \
    && mkdir -p /app/job_storage \
    && chown -R app:app /app

# Switch to non-root user
USER app

# Set environment variables
ENV PYTHONPATH=/app/src
ENV SHIFT_AGENT_PORT=8081
ENV LOG_LEVEL=INFO
ENV JOB_STORAGE_TYPE=filesystem
ENV JOB_STORAGE_DIR=/app/job_storage

# Expose port
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Run the application
CMD ["python", "-m", "shift_agent.api.server"]
