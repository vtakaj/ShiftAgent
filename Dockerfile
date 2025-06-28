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

# Install minimal system dependencies and Java runtime
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
COPY main.py ./
COPY mcp_server.py ./
COPY src/ ./src/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 app \
    && mkdir -p /app/job_storage \
    && chown -R app:app /app
USER app

# Set JAVA_HOME for runtime (will be dynamically set by the environment file)
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Health check using the correct port and endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Expose the correct port (8081 as per main.py)
EXPOSE 8081

# Run application with the correct entry point
CMD ["python", "main.py"]
