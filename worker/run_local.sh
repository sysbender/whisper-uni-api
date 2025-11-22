#!/bin/bash

# Script to run the Whisper Transcription Worker locally

echo "Starting worker..."
echo "Make sure Redis is running on localhost:6379"
echo ""

python -m worker.main

