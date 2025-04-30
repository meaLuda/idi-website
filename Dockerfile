FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    libmysqlclient-dev \  
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput --clear --no-post-process
RUN python manage.py collectstatic --noinput

# Port where the Django app runs
EXPOSE 8000

# Start the application
CMD ["gunicorn", "idi.wsgi:application", "--bind", "0.0.0.0:8080"]