#!/bin/bash
set -e

# Similar to setup_dev but assumes dependencies might be cached or less verbose
# We simply delegate to setup_dev.sh for consistency, as the "One Way To Do It" principle.

bash scripts/setup_dev.sh
