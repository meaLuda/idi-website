# Multi-stage build for optimized production image
FROM python:3.12-slim as builder

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
FROM python:3.12-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user for security
RUN groupadd -r django && useradd -r -g django django

# Set work directory
WORKDIR /app

# Copy project files
COPY --chown=django:django . .

# Collect static files
RUN python manage.py collectstatic --noinput
RUN python manage.py compress --force

# Create directories for media files with proper permissions
RUN mkdir -p /app/media /app/staticfiles /app/cache && \
    chown -R django:django /app/media /app/staticfiles /app/cache

# Switch to non-root user
USER django


# Port where the Django app runs
EXPOSE 8000

# Start the application with optimized gunicorn settings
CMD ["gunicorn", "idi.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--worker-connections", "1000", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--timeout", "30", \
     "--keep-alive", "5", \
     "--preload", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]