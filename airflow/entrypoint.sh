#!/bin/bash
set -e

airflow db migrate

# Recreate the admin user with the password from the environment so
# credentials are always in sync with .env regardless of prior state.
airflow users delete --username "${AIRFLOW_ADMIN_USERNAME}" 2>/dev/null || true
airflow users create \
  --username "${AIRFLOW_ADMIN_USERNAME}" \
  --password "${AIRFLOW_ADMIN_PASSWORD}" \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@databridge.io

airflow scheduler &
exec airflow webserver
