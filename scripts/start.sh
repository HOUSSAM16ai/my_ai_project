#!/bin/bash
set -e

# Standardized startup command using the Factory Pattern
exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
