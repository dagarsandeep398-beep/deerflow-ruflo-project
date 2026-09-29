#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from template. Please fill in API keys and secrets before running live mode."
fi

if command -v docker >/dev/null 2>&1; then
  docker compose up --build -d
  echo "The app is running in paper mode. Open http://localhost:8000"
else
  echo "Docker is not installed. Install Docker Desktop or Docker Engine first."
  exit 1
fi
