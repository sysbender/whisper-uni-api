#!/bin/bash

# Script to run the Whisper Transcription API locally

echo "Starting Redis..."
docker run -d -p 6379:6379 --name whisper-redis redis:7-alpine || docker start whisper-redis

echo "Waiting for Redis to be ready..."
sleep 2

echo "Starting API service..."
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "API service started with PID: $API_PID"
echo "API available at: http://localhost:8000"
echo ""
echo "To start the worker, run in another terminal:"
echo "  python -m worker.main"
echo ""
echo "Press Ctrl+C to stop the API service"

wait $API_PID

