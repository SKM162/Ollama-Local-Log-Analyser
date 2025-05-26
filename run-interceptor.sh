#!/bin/bash

# Default values
TARGET_URL="http://localhost:11434"
LOGS_DIR="./logs"
LISTEN_ADDR=":11435"

# Parse CLI arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -target) TARGET_URL="$2"; shift ;;
        -log) LOGS_DIR="$2"; shift ;;
        -listen) LISTEN_ADDR="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Kill existing interceptor processes
echo "Killing existing interceptor processes..."
ps aux | grep ollama-request-interceptor.go | grep -v grep | awk '{print $2}' | xargs kill -9

# Wait a moment to ensure clean termination
sleep 1

# Start new interceptor process in background with nohup and disown
echo "Starting new interceptor process..."
nohup go run ollama-request-interceptor.go -target "$TARGET_URL" -log "$LOGS_DIR" -listen "$LISTEN_ADDR" > interceptor.out 2>&1 &

# Disown the process
disown

echo "Interceptor started with:"
echo "  Target URL : $TARGET_URL"
echo "  Logs Dir   : $LOGS_DIR"
echo "  Listen Addr: $LISTEN_ADDR"
echo "  Logs written to interceptor.out"
