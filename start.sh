#!/bin/sh

# Run database migrations
echo "🔄 Running database migrations..."
poetry run alembic upgrade head

# Start the application
echo "🚀 Starting GameDex application..."
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8080 