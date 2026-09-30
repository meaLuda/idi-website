#!/bin/bash
set -e

# Function to wait for database
wait_for_db() {
    echo "Waiting for database connection..."
    until python -c "
import django
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'idi.settings')
django.setup()
from django.db import connections
from django.db.utils import OperationalError
try:
    db_conn = connections['default']
    db_conn.cursor()
    print('Database is ready!')
except OperationalError:
    sys.exit(1)
"; do
        echo "Database is unavailable - sleeping"
        sleep 1
    done
}

# Function to fix media permissions
fix_media_permissions() {
    echo "Checking and fixing media directory permissions..."
    
    # Always ensure proper permissions as root first (if we are root)
    if [ "$(id -u)" = "0" ]; then
        echo "Running as root, ensuring proper media directory setup..."
        
        # Create all necessary directories
        mkdir -p /app/media/uploads/team/shapes
        mkdir -p /app/media/uploads/projects/thumbnails
        mkdir -p /app/media/uploads/testimonials
        mkdir -p /app/media/uploads/programs/brochures
        mkdir -p /app/media/uploads/partners
        mkdir -p /app/media/uploads/clients
        
        # Set ownership and permissions
        chown -R django:django /app/media/uploads
        chmod -R 755 /app/media
        
        echo "Media directory permissions fixed"
    else
        # If not running as root, just check if we can write
        if [ -w /app/media ]; then
            echo "Media directory is writable"
            # Try to create subdirectories (they may already exist)
            mkdir -p /app/media/uploads/team/shapes 2>/dev/null || true
            mkdir -p /app/media/uploads/projects/thumbnails 2>/dev/null || true
            mkdir -p /app/media/uploads/testimonials 2>/dev/null || true
            mkdir -p /app/media/uploads/programs/brochures 2>/dev/null || true
            mkdir -p /app/media/uploads/partners 2>/dev/null || true
            mkdir -p /app/media/uploads/clients 2>/dev/null || true
        else
            echo "Warning: Media directory is not writable and not running as root!"
        fi
    fi
}

# Function to collect static files (WhiteNoise generates hashed + gzip/brotli variants).
#
# NOTE: no --clear. Clearing wipes the target dir first, which on a fresh/wrong-owned
# named volume triggers a permissions crash-loop. collectstatic is idempotent without it.
#
# The Dockerfile already runs collectstatic at build time, so the image ships a
# complete staticfiles tree and manifest. Repeating it at every container start
# reprocessed ~5,800 files (each gzipped AND brotli-compressed), which took over
# three minutes on a loaded host -- and because it runs before gunicorn binds,
# that was three minutes of 404s on every deploy and every rollback.
#
# So: skip when the image's own manifest is already present. Set
# FORCE_COLLECTSTATIC=true to override, which is what you want if /app/staticfiles
# is a volume that shadows the image's copy.
collect_static() {
    if [ "${FORCE_COLLECTSTATIC:-false}" != "true" ] \
       && [ -f /app/staticfiles/staticfiles.json ]; then
        echo "Static files already collected in the image; skipping (set FORCE_COLLECTSTATIC=true to force)."
        return 0
    fi
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
}


# Main execution
echo "Starting IDI Django application..."

# Wait for database
wait_for_db

# Apply database migrations (idempotent)
echo "Applying database migrations..."
python manage.py migrate --noinput

# Fix media permissions
fix_media_permissions

# Collect static files (in case of changes)
collect_static


echo "Starting gunicorn server..."

# Execute the main command
exec "$@"