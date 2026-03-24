#!/usr/bin/env bash
# run_local_stack.sh — start the full local stack with live reload
set -euo pipefail

echo "==> Starting full stack..."
docker compose up --build "$@"
