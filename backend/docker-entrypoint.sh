#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL to be ready..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "✅ PostgreSQL is ready"

mkdir -p /app/migrations/versions

# Step 1: Если миграций нет вообще — создаём начальную
if [ -z "$(find /app/migrations/versions -name '*.py' 2>/dev/null)" ]; then
  echo "📋 No migrations found — creating initial migration..."
  alembic revision --autogenerate -m "initial"
  echo "✅ Initial migration created"
else
  echo "📋 Existing migrations found"
fi

# Step 2: Применяем все ожидающие миграции
echo "⬆️  Applying migrations..."
if ! alembic upgrade head 2>/tmp/alembic_err.txt; then
  cat /tmp/alembic_err.txt

  if grep -q "Can't locate revision" /tmp/alembic_err.txt; then
    # В БД застрял revision которого нет в файлах — сбрасываем alembic_version
    echo "⚠️  Stale revision — resetting alembic_version..."
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
    # Плохая автомиграция без DEFAULT — удаляем ВСЕ файлы кроме initial
    # Alembic называет файлы {rev_id}_{message}.py, поэтому ищем по суффиксу
    echo "⚠️  NOT NULL migration error — removing bad migrations..."
    find /app/migrations/versions -name "*.py" ! -name "*_initial.py" -delete
    echo "Remaining migration files:"
    ls /app/migrations/versions/
    # Синхронизируем alembic_version с текущей цепочкой (только initial)
    echo "🔖 Stamping DB to head of remaining migration chain..."
    alembic stamp head
    # Генерируем заново — теперь модель содержит server_default, ошибки не будет
    echo "🔄 Regenerating migration with correct schema..."
    alembic revision --autogenerate -m "auto_$(date +%s)"
    alembic upgrade head

  else
    echo "❌ Unknown migration error — see above"
    exit 1
  fi
fi

# Step 3: После того как БД на head — проверяем новые изменения модели
echo "🔍 Checking for new model changes..."
if ! alembic check 2>/dev/null; then
  echo "🔄 New schema changes detected — generating migration..."
  alembic revision --autogenerate -m "auto_$(date +%s)"
  alembic upgrade head
  echo "✅ New migration applied"
else
  echo "✅ Schema is up to date"
fi

echo "✅ Migrations done"
echo "🚀 Starting backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
