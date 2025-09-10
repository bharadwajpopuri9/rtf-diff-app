#!/bin/bash

# RTF Comparison App - Production Startup Script

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    venv/bin/pip install -r requirements.txt
fi

# Set environment variables for production
export PYTHONPATH="$(pwd)"
export FLASK_ENV="production"
export SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"

# Production server settings
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-4}"

echo "Starting RTF Comparison Web Application (Production)..."
echo "Server will be available at: http://$HOST:$PORT"
echo "Workers: $WORKERS"
echo "Press Ctrl+C to stop the server"
echo ""

# Install gunicorn if not present
venv/bin/pip install gunicorn

# Start the production server
venv/bin/gunicorn "app:app" \
    --bind "$HOST:$PORT" \
    --workers "$WORKERS" \
    --timeout 300 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile -
