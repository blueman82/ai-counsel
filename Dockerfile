FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and transcripts
RUN mkdir -p /app/logs /app/transcripts

# Set environment variables
ENV PYTHONUNBUFFERED=1

# The MCP server uses stdio transport
ENTRYPOINT ["python", "server.py"]
