#!/bin/bash
set -e

echo "========================================"
echo "  Trio Snacks - Starting Application"
echo "========================================"

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    exit 1
fi

if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

if ! python3 -c "import flask" &> /dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo "Starting Trio Snacks at http://localhost:5000 ..."
python3 app.py
