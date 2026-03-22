#!/bin/bash
set -e

if [ ! -f .env ]; then
  cp .env.example .env
  # Generate a real secret key so it works out of the box
  SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  sed -i.bak "s/SECRET_KEY=changeme/SECRET_KEY=$SECRET/" .env && rm -f .env.bak
  echo ".env created from .env.example"
else
  # Add any keys present in .env.example that are missing from .env
  while IFS= read -r line; do
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    key="${line%%=*}"
    if ! grep -q "^${key}=" .env; then
      echo "$line" >> .env
      echo "Added missing key to .env: $key"
    fi
  done < .env.example
fi

git config core.hooksPath .githooks

docker compose up --build "$@"
