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
    
    # Create media directory if it doesn't exist
    mkdir -p /app/media
    
    # Check if media directory is writable
    if [ -w /app/media ]; then
        echo "Media directory is writable"
    else
        echo "Warning: Media directory is not writable!"
        # If running as root, fix permissions
        if [ "$(id -u)" = "0" ]; then
            echo "Running as root, fixing permissions..."
            chmod -R 755 /app/media
            chown -R django:django /app/media
        fi
    fi
    
    # Create uploads subdirectory for CKEditor
    mkdir -p /app/media/uploads
    
    # Set proper permissions for uploaded files
    find /app/media -type d -exec chmod 755 {} \;
    find /app/media -type f -exec chmod 644 {} \; 2>/dev/null || true
}

# Function to run migrations
run_migrations() {
    echo "Running database migrations..."
    python manage.py migrate --noinput
}

# Function to collect static files
collect_static() {
    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear
    python manage.py compress --force
}

# Main execution
echo "Starting IDI Django application..."

# Wait for database
wait_for_db

# Fix media permissions
fix_media_permissions

# Run migrations
run_migrations

# Collect static files (in case of changes)
collect_static

# Create superuser if it doesn't exist (optional)
python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'idi.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    print('Creating default admin user...')
    User.objects.create_superuser('admin', 'admin@idi.africa', 'admin123')
    print('Default admin user created: admin/admin123')
else:
    print('Admin user already exists')
" || true

echo "Starting gunicorn server..."

# Execute the main command
exec "$@"