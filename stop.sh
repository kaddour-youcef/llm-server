#!/bin/bash
set -e

# List of container names in this stack
containers=(
  vllm
  llm-server-db
  llm-server-redis
  gateway
  llm-server-admin
)

echo "Stopping and removing containers..."
for c in "${containers[@]}"; do
  if [ "$(docker ps -aq -f name=^${c}$)" ]; then
    docker stop $c >/dev/null 2>&1 || true
    docker rm $c >/dev/null 2>&1 || true
    echo " - Removed $c"
  else
    echo " - $c not found"
  fi
done

echo "All containers stopped and removed."
echo "Postgres volume (pgdata) preserved."
