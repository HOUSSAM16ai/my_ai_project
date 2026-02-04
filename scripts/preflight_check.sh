#!/bin/bash
mkdir -p reports
echo "Running pytest..."
python -m pytest -q > reports/pytest_preflight.log 2>&1
echo "Running ruff..."
ruff check . > reports/ruff_preflight.txt 2>&1
echo "Checking docker-compose config..."
docker-compose config > reports/docker_config.txt 2>&1
echo "Preflight checks complete."
