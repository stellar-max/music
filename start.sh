#!/bin/bash
# start.sh - VPS/Manual startup script

echo "🚀 Starting swagPlayer..."

# Load environment variables
if [ -f .env ]; then
    echo "📝 Loading .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️ Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Run migrations (if any)
echo "📦 Running migrations..."
python -c "from app import init_db; init_db()"

# Start application
echo "🎵 Starting application..."
if [ "$1" = "dev" ]; then
    python app.py
else
    gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:5024 app:app
fi
