# Whisper Universal API

A universal transcription API service supporting multiple Whisper variants (WhisperX and whisper-timestamped) with a clean, modular architecture.

## Project Structure

This project is organized as two separate services:

```
whisper-uni-api/
├── api/                    # API service (FastAPI)
│   ├── pyproject.toml      # API dependencies (uv)
│   ├── Dockerfile          # API container
│   ├── run_local.sh        # Local development script (Linux/Mac)
│   ├── run_local.bat       # Local development script (Windows)
│   └── ...
├── worker/                  # Worker service (RQ)
│   ├── pyproject.toml     # Worker dependencies (uv)
│   ├── Dockerfile.whisperx # WhisperX worker container
│   ├── Dockerfile.timestamped # whisper-timestamped worker container
│   ├── run_local.sh        # Local development script (Linux/Mac)
│   ├── run_local.bat       # Local development script (Windows)
│   └── ...
├── docker-compose.yml      # Orchestration for all services
└── README.md              # This file
```

## Services

### API Service (`api/`)
- FastAPI-based REST API
- Handles file uploads and job queuing
- Manages job status and results
- **Dependencies**: FastAPI, Uvicorn, Redis, RQ, Pydantic

### Worker Service (`worker/`)
- RQ-based background worker
- Supports multiple Whisper engines:
  - **WhisperX**: Word-level timestamps and speaker diarization
  - **whisper-timestamped**: Lightweight timestamped transcription
- **Dependencies**: Redis, RQ

## Quick Start

### Prerequisites
- Docker and Docker Compose
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Python 3.11+

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The API will be available at `http://localhost:8000`

### Local Development

#### API Service

```bash
cd api

# Install dependencies with uv
uv sync

# Run the API
uvicorn api.main:app --reload

# Or use the convenience script
./run_local.sh  # Linux/Mac
run_local.bat   # Windows
```

#### Worker Service

```bash
cd worker

# Install dependencies with uv
uv sync

# Run the worker
python -m worker.main

# Or use the convenience script
./run_local.sh  # Linux/Mac
run_local.bat   # Windows
```

**Note**: Make sure Redis is running before starting the worker:
```bash
docker run -d -p 6379:6379 --name whisper-redis redis:7-alpine
```

## API Endpoints

- `POST /transcribe` - Upload audio and enqueue transcription job
- `GET /status/{job_id}` - Query job status and retrieve results
- `GET /health` - Health check endpoint

## Development

### Installing Dependencies

Both services use `uv` for dependency management:

```bash
# API service
cd api
uv sync

# Worker service
cd worker
uv sync
```

### Running Tests

```bash
# API tests
cd api
uv run pytest

# Worker tests
cd worker
uv run pytest
```

## Docker Images

- **API**: Built from `python:3.11-slim` with uv
- **Worker (WhisperX)**: Built from `ghcr.io/jim60105/whisperx:no_model`
- **Worker (whisper-timestamped)**: Built from `linto-ai/whisper-timestamped:latest`

## Architecture

- **API Service**: Handles HTTP requests, file uploads, and job management
- **Worker Service**: Processes transcription jobs asynchronously using Redis Queue
- **Redis**: Message broker and job queue
- **Shared Volumes**: For file uploads and transcription outputs

## License

[Your License Here]
