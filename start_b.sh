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
  -p 5432:5432 \
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

# 2. Start Redis
docker run -d \
  --name llm-server-redis \
  --network llm-net \
  -p 6379:6379 \
  --health-cmd="redis-cli ping || exit 1" \
  --health-interval=5s \
  --health-timeout=3s \
  --health-retries=5 \
  redis:7

# Wait until Redis is healthy
until [ "$(docker inspect --format='{{.State.Health.Status}}' llm-server-redis)" == "healthy" ]; do
  sleep 3
done
echo "✅ Redis is healthy"

# 3. Start vLLM (with GPU & HuggingFace token)
docker run -d \
  --name vllm \
  --env-file .env \
  --network llm-net \
  --runtime=nvidia \
  --gpus device=0 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v /home/rootxe/extend-qnap/mlstorage-v3/youcef_kaddour_workspace:/workspace \
  --ipc=host \
  -p 8000 \
  vllm/vllm-openai:a100-cuda12.0 \
    --model mistralai/Mistral-Small-3.2-24B-Instruct-2506 \
    --tokenizer-mode mistral \
    --config-format mistral \
    --load-format mistral \
    --tool-call-parser mistral \
    --enable-auto-tool-choice \
    --limit-mm-per-prompt 'image=10' \
    --tensor-parallel-size 1 \
    --download-dir /workspace

# Wait until vLLM port is open inside the container


# 4. Build and run Gateway
docker build -t gateway ./gateway
docker run -d \
  --name gateway \
  --network llm-net \
  --env-file .env \
  -p 8080:8080 \
  gateway

# Wait until gateway port is open on host


# 5. Build and run Admin
docker build -t llm-server-admin ./admin
docker run -d \
  --name llm-server-admin \
  --network llm-net \
  --env-file .env \
  -e GATEWAY_URL=http://gateway:8080 \
  -p 8181:8501 \
  llm-server-admin

echo "🚀 All services started successfully:"
echo "   - Gateway: http://localhost:8080"
echo "   - Admin:   http://localhost:8181"
