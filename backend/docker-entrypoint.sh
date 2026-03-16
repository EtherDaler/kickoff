#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL to be ready..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "✅ PostgreSQL is ready"

mkdir -p /app/migrations/versions

# Создаём начальную миграцию если её ещё нет
if [ -z "$(find /app/migrations/versions -name '*.py' 2>/dev/null)" ]; then
  echo "📋 No migrations found — creating initial migration..."
  alembic revision --autogenerate -m "initial"
  echo "✅ Initial migration created"
else
  echo "📋 Existing migrations found"
fi

# Применяем миграции
echo "⬆️  Applying migrations..."
if ! alembic upgrade head 2>/tmp/alembic_err.txt; then
  # Если в БД застрял старый revision — сбрасываем и мигрируем заново
  if grep -q "Can't locate revision" /tmp/alembic_err.txt; then
    echo "⚠️  Stale revision detected — resetting alembic_version..."
    python3 -c "
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def reset():
    engine = create_async_engine(os.environ['DATABASE_URL'])
    async with engine.begin() as conn:
        await conn.execute(text('DROP TABLE IF EXISTS alembic_version'))
    await engine.dispose()

asyncio.run(reset())
"
    echo "🔄 Retrying migrations..."
    alembic upgrade head
  else
    cat /tmp/alembic_err.txt
    exit 1
  fi
fi

echo "✅ Migrations done"
echo "🚀 Starting backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
