FROM python:3.12-slim

WORKDIR /app

# Install dependencies first — Docker caches this layer separately from your
# source code, so rebuilds are fast as long as requirements.txt doesn't change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code after deps so code changes don't bust the pip cache layer
COPY . .

# uvicorn is the ASGI server that runs FastAPI.
# --host 0.0.0.0 makes it reachable outside the container (default is 127.0.0.1).
# --reload watches for file changes and restarts automatically — dev only.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
