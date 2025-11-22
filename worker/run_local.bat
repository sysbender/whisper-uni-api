@echo off
REM Script to run the Whisper Transcription Worker locally on Windows

echo Starting worker...
echo Make sure Redis is running on localhost:6379
echo.

python -m worker.main

pause

