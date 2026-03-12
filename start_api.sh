#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting Healthcare API..."

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install required packages
echo "Installing dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn faker requests

# Start the FastAPI server
echo "Starting the API server on http://127.0.0.1:8000"
echo "Press Ctrl+C to stop the server."
uvicorn main:app --reload