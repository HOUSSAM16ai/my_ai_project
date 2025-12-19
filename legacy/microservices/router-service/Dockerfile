# AI Router Service Dockerfile
# Distroless base for security and minimal attack surface

FROM python:3.12-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage - Distroless
FROM gcr.io/distroless/python3-debian12:nonroot

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/nonroot/.local

# Copy application code
COPY main.py .

# Set environment
ENV PATH=/home/nonroot/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

# Run as non-root user
USER nonroot

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "main.py"]
