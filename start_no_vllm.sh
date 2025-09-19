#!/bin/bash
set -e

# Create network & volume if not already existing
docker network create llm-net || true
docker volume create pgdata || true

# Helper function to wait until a TCP port is open
wait_for_port() {
  local host=$1
  local port=$2
  echo "⏳ Waiting for $host:$port to be available..."
  until nc -z "$host" "$port"; do
    sleep 3
  done
  echo "✅ $host:$port is available"
}

# 1. Start Postgres
docker run -d \
  --name llm-server-db \
  --network llm-net \
  -e POSTGRES_DB=gateway \
  -e POSTGRES_USER=gateway \
  -e POSTGRES_PASSWORD=gateway_password \
  -v pgdata:/var/lib/postgresql/data \
  -p 5252:5252 \
  --health-cmd="pg_isready -U gateway -d gateway || exit 1" \
  --health-interval=5s \
  --health-timeout=3s \
  --health-retries=5 \
  postgres:15

# Wait until Postgres is healthy
until [ "$(docker inspect --format='{{.State.Health.Status}}' llm-server-db)" == "healthy" ]; do
  sleep 3
done
echo "✅ Postgres is healthy"

# Wait until vLLM port is open inside the container


# 4. Build and run Gateway
docker build -t gateway ./gateway
docker run -d \
  --name gateway \
  --network llm-net \
  --env-file .env \
  -p 8080:8080 \
  gateway


echo "🚀 All services started successfully:"
echo "   - Gateway: http://localhost:8080"
echo "   - Admin:   http://localhost:8181"

