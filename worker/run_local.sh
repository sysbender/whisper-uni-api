#!/bin/bash

# Script to run the Whisper Transcription Worker locally

echo "Starting worker..."
echo "Make sure Redis is running on localhost:6379"
echo ""

export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
#python -m worker.main
uv run --env-file .env -m worker.main

