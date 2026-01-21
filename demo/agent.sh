#!/bin/bash

# Wrapper for the Python Interactive CLI
cd "$(dirname "$0")"

# Ensure venv is active (Agent Service uses the same venv, usually in a2a/a2a-service)
# But for CLI dependencies (rich, prompt_toolkit), we installed them in a2a/a2a-service/venv via pip earlier.
if [ -f "../a2a/a2a-service/venv/bin/activate" ]; then
    source ../a2a/a2a-service/venv/bin/activate
else
    echo "❌ Error: Virtual environment not found. Did you run ./start.sh?"
    exit 1
fi

# Run the Python CLI
python3 cli.py
