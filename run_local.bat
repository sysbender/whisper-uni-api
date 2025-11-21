@echo off
REM Script to run the Whisper Transcription API locally on Windows

echo Starting Redis...
docker run -d -p 6379:6379 --name whisper-redis redis:7-alpine 2>nul || docker start whisper-redis

echo Waiting for Redis to be ready...
timeout /t 2 /nobreak >nul

echo Starting API service...
start "Whisper API" cmd /k "uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo API service starting...
echo API will be available at: http://localhost:8000
echo.
echo To start the worker, open another terminal and run:
echo   python -m worker.main
echo.
pause

