#!/bin/bash
set -e
echo "🚀 Starting backend server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
