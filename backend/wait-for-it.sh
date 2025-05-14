#!/bin/sh
# wait-for-it.sh

echo "Waiting for database..."
timeout=60

while ! nc -z db 3306; do
  timeout=$((timeout - 1))
  if [ "$timeout" -eq 0 ]; then
    echo "Database connection timeout!"
    exit 1
  fi
  echo "Database not ready yet, waiting... ($timeout seconds left)"
  sleep 1
done

echo "Database is available, starting app..."
exec "$@"