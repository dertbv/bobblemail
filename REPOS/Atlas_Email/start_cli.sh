#!/bin/bash
# Start Atlas Email CLI Interface

echo "🚀 Starting Atlas Email CLI..."
cd "$(dirname "$0")"
export PYTHONPATH=./src:$PYTHONPATH
python3 src/atlas_email/cli/main.py