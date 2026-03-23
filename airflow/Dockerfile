FROM apache/airflow:2.10.2

# The postgres provider adds PostgresHook, PostgresOperator, and the
# connection type used by our DAGs to talk to the app database.
RUN pip install --no-cache-dir apache-airflow-providers-postgres
