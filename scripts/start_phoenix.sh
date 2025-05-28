#!/bin/bash

# Set Phoenix collector endpoint
export PHOENIX_COLLECTOR_ENDPOINT="http://localhost:6006"

# Start Arize Phoenix server
echo "Starting Arize Phoenix server..."
echo "Phoenix collector endpoint: $PHOENIX_COLLECTOR_ENDPOINT"
phoenix serve 