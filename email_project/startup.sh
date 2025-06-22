#!/bin/bash
# Production startup script for Email Filter

set -e

echo "🚀 Starting Email Filter Application..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! pg_isready -h postgres -p 5432 -U emailuser; do
    echo "Database not ready, waiting..."
    sleep 2
done
echo "✅ Database ready"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
while ! redis-cli -h redis ping; do
    echo "Redis not ready, waiting..."
    sleep 2
done
echo "✅ Redis ready"

# Run database migrations if needed
echo "🔄 Running database setup..."
python -c "
from database import db
try:
    db.get_connection()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Start the application
echo "🎯 Starting web application..."
exec python web_app.py