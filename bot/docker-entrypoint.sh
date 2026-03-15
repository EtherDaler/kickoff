#!/bin/sh
set -e

echo "⏳ Waiting for backend to be ready..."

while ! nc -z backend 8000; do
  sleep 2
done

echo "✅ Backend is ready"
echo "🤖 Starting Telegram bot..."
exec python -m bot.main
