# Guardrails Service Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM gcr.io/distroless/python3-debian12:nonroot

WORKDIR /app

COPY --from=builder /root/.local /home/nonroot/.local
COPY main.py .

ENV PATH=/home/nonroot/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

USER nonroot

EXPOSE 8000

CMD ["python", "main.py"]
