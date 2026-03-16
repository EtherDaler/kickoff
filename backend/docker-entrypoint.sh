#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL to be ready..."

while ! nc -z postgres 5432; do
  sleep 1
done

echo "✅ PostgreSQL is ready — running migrations"

# Убеждаемся что папка versions существует
mkdir -p /app/migrations/versions

# Если нет ни одного файла миграции — создаём первую
if [ -z "$(find /app/migrations/versions -name '*.py' 2>/dev/null)" ]; then
  echo "📋 No migrations found — creating initial migration..."
  alembic revision --autogenerate -m "initial"
  echo "✅ Initial migration created"
else
  echo "📋 Existing migrations found"
fi

# Применяем все pending миграции
echo "⬆️  Applying migrations..."
alembic upgrade head

echo "✅ Migrations done"
echo "🚀 Starting backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
