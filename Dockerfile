# Dockerfile for Project P_311: Knowledge driven IoT fault diagnosis assistant
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose HTTP port
EXPOSE 8000

# Run continuous 24/7 assistant service
CMD ["python", "main.py"]
