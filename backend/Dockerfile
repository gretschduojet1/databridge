FROM python:3.12-slim

WORKDIR /app

# Install dependencies first — Docker caches this layer separately from your
# source code, so rebuilds are fast as long as requirements.txt doesn't change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code after deps so code changes don't bust the pip cache layer
COPY . .

# Runs migrations then starts uvicorn
CMD ["bash", "entrypoint.sh"]
