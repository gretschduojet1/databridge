#!/bin/bash
set -e

if [ ! -f .env ]; then
  cp .env.example .env
  echo ".env created from .env.example"
fi

docker compose up --build "$@"
