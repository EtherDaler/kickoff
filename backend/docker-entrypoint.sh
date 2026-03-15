#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL to be ready..."

while ! nc -z postgres 5432; do
  sleep 1
done

echo "✅ PostgreSQL is ready — running migrations"

# Если папка versions пустая — создаём первую миграцию
if [ -z "$(ls -A migrations/versions/*.py 2>/dev/null)" ]; then
  echo "📋 No migrations found — creating initial migration..."
  alembic revision --autogenerate -m "initial"
  echo "✅ Initial migration created"
else
  echo "📋 Existing migrations found — skipping creation"
fi

# Применяем все pending миграции
echo "⬆️  Applying migrations..."
alembic upgrade head

# Проверяем нет ли новых изменений схемы (актуально при hot-reload)
if alembic check 2>/dev/null; then
  echo "✅ Schema is up to date"
else
  echo "🔄 Schema changes detected — creating new migration..."
  alembic revision --autogenerate -m "auto_$(date +%Y%m%d_%H%M%S)"
  alembic upgrade head
  echo "✅ New migration applied"
fi

echo "🚀 Starting backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
