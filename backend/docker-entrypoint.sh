#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL to be ready..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "✅ PostgreSQL is ready"

mkdir -p /app/migrations/versions

# Создаём начальную миграцию если её ещё нет, иначе проверяем наличие новых изменений схемы
if [ -z "$(find /app/migrations/versions -name '*.py' 2>/dev/null)" ]; then
  echo "📋 No migrations found — creating initial migration..."
  alembic revision --autogenerate -m "initial"
  echo "✅ Initial migration created"
else
  echo "📋 Existing migrations found — checking for new schema changes..."
  if ! alembic check 2>/dev/null; then
    echo "🔄 New schema changes detected — generating migration..."
    alembic revision --autogenerate -m "auto_$(date +%s)"
    echo "✅ New migration created"
  else
    echo "✅ Schema is up to date"
  fi
fi

# Применяем миграции
echo "⬆️  Applying migrations..."
if ! alembic upgrade head 2>/tmp/alembic_err.txt; then
  if grep -q "Can't locate revision" /tmp/alembic_err.txt; then
    # Застрял старый revision в БД — сбрасываем и мигрируем заново
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
    echo "🔄 Retrying after stale revision reset..."
    alembic revision --autogenerate -m "recovery_$(date +%s)"
    alembic upgrade head
  elif grep -qE "NotNullViolationError|contains null values|not-null constraint|violates not-null" /tmp/alembic_err.txt; then
    # Сломанная auto-миграция без server_default — удаляем и пересоздаём
    echo "⚠️  NOT NULL migration error — removing bad auto-migration and regenerating..."
    find /app/migrations/versions -name "auto_*.py" -delete
    alembic revision --autogenerate -m "auto_$(date +%s)"
    alembic upgrade head
  else
    cat /tmp/alembic_err.txt
    exit 1
  fi
fi

echo "✅ Migrations done"
echo "🚀 Starting backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
