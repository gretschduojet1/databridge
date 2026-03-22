#!/bin/bash
set -e

if [ ! -f .env ]; then
  cp .env.example .env
  echo ".env created from .env.example"
else
  # Forward any keys present in .env.example that are missing from .env
  while IFS= read -r line; do
    # Skip comments and blank lines
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    key="${line%%=*}"
    if ! grep -q "^${key}=" .env; then
      echo "$line" >> .env
      echo "Added missing key to .env: $key"
    fi
  done < .env.example
fi

docker compose up --build "$@"
