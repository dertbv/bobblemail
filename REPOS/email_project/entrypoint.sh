#!/bin/bash
# Docker entrypoint script

set -e

# Function to check if a service is ready
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    
    echo "Waiting for $service at $host:$port..."
    while ! nc -z $host $port; do
        sleep 1
    done
    echo "$service is ready!"
}

# Install netcat for service checks
apt-get update && apt-get install -y netcat-openbsd

# Wait for required services
if [ "$DATABASE_URL" ]; then
    wait_for_service postgres 5432 "PostgreSQL"
fi

if [ "$REDIS_URL" ]; then
    wait_for_service redis 6379 "Redis"
fi

# Execute the main command
exec "$@"