# Dockerfile for AI Service - v4.0 (Simplified & Direct Execution)
FROM python:3.12-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

# Install postgresql-client for database debugging
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /code/requirements.txt

COPY ./ /code/

EXPOSE 8000

# Definitive command to start the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
