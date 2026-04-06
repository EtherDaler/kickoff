#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL to be ready..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "✅ PostgreSQL is ready"

mkdir -p /app/migrations/versions

# Step 1: If no migration files exist at all — create the initial one
if [ -z "$(find /app/migrations/versions -name '*.py' 2>/dev/null)" ]; then
  echo "📋 No migrations found — creating initial migration..."
  alembic revision --autogenerate -m "initial"
  echo "✅ Initial migration created"
else
  echo "📋 Existing migrations found"
fi

# Step 2: Apply all existing pending migrations
echo "⬆️  Applying migrations..."
if ! alembic upgrade head 2>/tmp/alembic_err.txt; then
  if grep -q "Can't locate revision" /tmp/alembic_err.txt; then
    # Stale revision in DB — reset alembic_version and retry
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
    # Bad auto-migration missing server_default — delete it and regenerate
    echo "⚠️  NOT NULL migration error — removing bad auto-migration and regenerating..."
    find /app/migrations/versions -name "auto_*.py" -delete
    alembic revision --autogenerate -m "auto_$(date +%s)"
    alembic upgrade head
  else
    cat /tmp/alembic_err.txt
    exit 1
  fi
fi

# Step 3: Only after DB is at head — check for new model changes not yet in a migration
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
