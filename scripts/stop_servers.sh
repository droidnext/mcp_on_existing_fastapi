#!/bin/bash

echo "Stopping servers..."

# Function to find and kill process by port
kill_process_by_port() {
    local port=$1
    local process_name=$2
    
    # Find PID using port
    local pid=$(lsof -ti :$port)
    
    if [ -n "$pid" ]; then
        echo "Stopping $process_name (PID: $pid) on port $port..."
        kill $pid
        # Wait for process to terminate
        sleep 2
        # Force kill if still running
        if ps -p $pid > /dev/null; then
            echo "Force stopping $process_name..."
            kill -9 $pid
        fi
    else
        echo "$process_name is not running on port $port"
    fi
}

# Stop FastAPI server (port 8000)
kill_process_by_port 8000 "FastAPI server"

# Stop Arize Phoenix server (port 6006)
kill_process_by_port 6006 "Arize Phoenix server"

echo "Servers stopped successfully!" 