# Dockerfile for AI Service - v4.0 (Simplified & Direct Execution)
FROM python:3.12-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

# We still need postgresql-client if we ever want to debug DB issues from inside
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /code/requirements.txt

COPY ./ /code/

# --- THE SUPERCHARGED FIX ---
# We have removed the `RUN chmod +x` line, as the entrypoint.sh no longer exists.
# We have also removed the old `CMD` line.

EXPOSE 8000

# This is now the definitive command to start the service.
# Docker-compose will execute this directly.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]