#!/bin/bash

# RTF Comparison App - Startup Script

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    venv/bin/pip install -r requirements.txt
fi

# Set environment variables
export PYTHONPATH="$(pwd)"
export FLASK_APP="app.py"
export FLASK_ENV="development"

echo "Starting RTF Comparison Web Application..."
echo "Access the app at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask development server
venv/bin/python -m flask run --host=0.0.0.0 --port=5000
