# Multi-stage build for optimized production image
FROM python:3.12-slim AS builder

# Install uv for faster package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies using uv globally
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Production stage
FROM python:3.12-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Give the non-root django user a writable HOME so tools that touch ~/.cache/.config
# (e.g. fontconfig via Pillow, matplotlib) don't crash when /home isn't writable on
# a fresh volume. /tmp is always writable in the container.
ENV HOME=/tmp

# Install runtime dependencies only (curl is used by the compose healthcheck)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user with specific UID/GID to match host permissions
RUN groupadd -g 1000 django && useradd -u 1000 -g 1000 -r django

# Set work directory
WORKDIR /app

# Copy project files
COPY --chown=django:django . .

# Copy and make entrypoint script executable
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create directories for media files with proper permissions
RUN mkdir -p /app/media /app/staticfiles /app/cache && \
    chown -R django:django /app/media /app/staticfiles /app/cache && \
    chmod -R 755 /app/media

# Collect static files (hashed + gzip + brotli via WhiteNoise; runs before switching users)
RUN python manage.py collectstatic --noinput

# Port where the Django app runs
EXPOSE 8000

# Container healthcheck hits the lightweight /health/ endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/', timeout=4).status==200 else 1)"

# Use entrypoint script (runs as root initially)
ENTRYPOINT ["/docker-entrypoint.sh"]

# Start the application with optimized gunicorn settings (switches to django user in entrypoint).
# --worker-tmp-dir /dev/shm keeps gunicorn's heartbeat file off slow disk (avoids worker stalls).
CMD ["gunicorn", "idi.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "sync", "--worker-connections", "1000", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "30", "--keep-alive", "5", "--preload", "--worker-tmp-dir", "/dev/shm", "--access-logfile", "-", "--error-logfile", "-"]