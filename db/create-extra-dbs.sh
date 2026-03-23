#!/bin/bash
# Creates extra databases needed by services that share the Postgres instance.
# Runs automatically on first container start (empty volume) via
# /docker-entrypoint-initdb.d — Postgres executes every .sh/.sql file there
# in filename order, which is why this is prefixed 00-.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE airflow;
    GRANT ALL PRIVILEGES ON DATABASE airflow TO $POSTGRES_USER;
EOSQL
