#!/bin/bash
# Mimi Robot - Start Backend Server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"

echo "🧸 Starting Mimi Robot Backend Server..."
echo "========================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.9+"
    exit 1
fi

# Check virtual environment
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$BACKEND_DIR/venv"
fi

# Activate venv
source "$BACKEND_DIR/venv/bin/activate"

# Check dependencies
if [ ! -f "$BACKEND_DIR/venv/installed" ]; then
    echo "📦 Installing dependencies..."
    pip install -r "$BACKEND_DIR/requirements.txt"
    pip install edge-tts
    touch "$BACKEND_DIR/venv/installed"
fi

# Check .env
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "⚠️  No .env file found!"
    echo "   Copy .env.example to .env and add your API keys"
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    echo "   Please edit $BACKEND_DIR/.env"
    exit 1
fi

# Start server
echo ""
echo "🚀 Starting server..."
echo "   URL: http://0.0.0.0:8080"
echo "   WebSocket: ws://0.0.0.0:8080/ws"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "$BACKEND_DIR/src"
python main.py
