#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the project root directory (parent of scripts directory)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root directory
cd "$PROJECT_ROOT"

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Start FastAPI server
echo "Starting FastAPI server..."
echo "Project root: $PROJECT_ROOT"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 