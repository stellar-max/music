#!/bin/bash
# scripts/setup_env.sh - Auto-detect environment

echo "🔍 Detecting deployment environment..."

# Detect platform
if [ -n "$RENDER" ]; then
    echo "✅ Render detected"
    export WEBAPP_URL="https://${RENDER_EXTERNAL_HOSTNAME}"
    export PORT=${PORT:-10000}
elif [ -n "$DYNO" ]; then
    echo "✅ Heroku detected"
    export WEBAPP_URL="https://${HEROKU_APP_NAME}.herokuapp.com"
    export PORT=${PORT:-5000}
elif [ -n "$VERCEL" ]; then
    echo "✅ Vercel detected"
    export WEBAPP_URL="https://${VERCEL_URL}"
elif [ -f "/.dockerenv" ]; then
    echo "✅ Docker detected"
    export WEBAPP_URL=${WEBAPP_URL:-http://localhost:5024}
    export PORT=${PORT:-5024}
else
    echo "✅ Local environment detected"
    export WEBAPP_URL=${WEBAPP_URL:-http://localhost:5024}
    export PORT=${PORT:-5024}
fi

echo "🌐 WEBAPP_URL: $WEBAPP_URL"
echo "🔌 PORT: $PORT"

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    sed -i "s|WEBAPP_URL=.*|WEBAPP_URL=${WEBAPP_URL}|g" .env
    sed -i "s|PORT=.*|PORT=${PORT}|g" .env
fi
