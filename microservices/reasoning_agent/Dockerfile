# Reasoning Agent Dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app"

# Install basics
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Code (Constructing package structure from service context)
COPY . /app/microservices/reasoning_agent

# Run
CMD ["uvicorn", "microservices.reasoning_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
