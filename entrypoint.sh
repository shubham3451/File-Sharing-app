#!/bin/bash

set -e

echo "Waiting for PostgreSQL to be ready..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL is up!"

# Migrate and collect static files
echo "Running migrations..."
python manage.py migrate

# Uncomment if needed:
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

echo "Starting Gunicorn server..."
gunicorn Project.wsgi:application --bind 0.0.0.0:8000
