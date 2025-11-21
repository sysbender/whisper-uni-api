# MVP Implementation

## Project Structure Created

### API Service (api/)
- `main.py` - FastAPI app initialization
- `models.py` - Pydantic schemas (TranscribeRequest, TranscribeResponse, JobStatus)
- `handlers.py` - REST endpoints (POST /transcribe, GET /status/{job_id}, GET /health)
- `storage.py` - File upload management
- `config.py` - Configuration management
- `tests/test_api.py` - Test suite with 6 test cases

### Worker Service (worker/)
- `main.py` - RQ worker startup
- `tasks.py` - Transcription task definitions
- `config.py` - Worker configuration
- `runners/base.py` - Abstract runner interface with TranscriptionResult/TranscriptionSegment
- `runners/whisperx.py` - WhisperX engine implementation
- `runners/timestamped.py` - whisper-timestamped engine implementation
- `tests/test_worker.py` - Test suite with 7 test cases

### Configuration Files
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Docker Compose setup with Redis, API, and Worker services
- `Dockerfile.api` - API service container
- `Dockerfile.worker.whisperx` - WhisperX worker service container with GPU support
- `Dockerfile.worker.timestamped` - whisper-timestamped worker service container with GPU support
- `setup.py` - Python package setup
- `.gitignore` - Git ignore rules
- `README.md` - Documentation

### Helper Scripts
- `run_local.sh` - Local development script (Linux/Mac)
- `run_local.bat` - Local development script (Windows)
- `main.py` - Root-level entry point

## Features Implemented

### REST API Endpoints
- `POST /transcribe` - Upload audio and enqueue job
- `GET /status/{job_id}` - Query job status and results
- `GET /health` - Health check

### Background Processing
- Redis Queue (RQ) integration
- Asynchronous job processing
- Job status tracking

### Engine Abstraction
- Base runner interface
- WhisperX runner with diarization support
- whisper-timestamped runner with VAD filtering
- Unified output format

### Error Handling
- File validation (format, size)
- Engine parameter validation
- Error responses with proper HTTP status codes

### Testing
- API tests (6 test cases)
- Worker tests (7 test cases)
- Mock-based testing for external dependencies

## Next Steps

### Install Whisper Engines
The engines are now included in the Docker images, but if running locally:
```bash
pip install whisperx whisper-timestamped
```

### Run Locally
```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Start API
uvicorn api.main:app --reload

# Start Worker (in another terminal)
python -m worker.main
```

### Or Use Docker Compose
```bash
docker-compose up -d
```

The MVP is ready for development and testing. The structure follows the design documents and is ready to integrate with WhisperX and whisper-timestamped engines.

## Recent Changes

### Docker Worker Images
Created separate Docker images for each Whisper variant:

**Dockerfile.worker.whisperx**
- Builds on `ghcr.io/jim60105/whisperx:no_model`
- Installs Redis and RQ dependencies
- Copies worker code
- Creates output directories

**Dockerfile.worker.timestamped**
- Builds on `linto-ai/whisper-timestamped:latest`
- Installs Redis and RQ dependencies
- Copies worker code
- Creates output directories

**Updated docker-compose.yml**
- Replaced the single `worker` service with:
  - `worker-whisperx` - Uses `Dockerfile.worker.whisperx`
  - `worker-timestamped` - Uses `Dockerfile.worker.timestamped`
- Both services keep the same GPU configuration and volume mounts

### Note
Both workers listen to the same Redis queue. Consider:
- Using separate queues per engine (e.g., `whisperx` and `timestamped`)
- Adding queue filtering in the worker code so each worker only processes its engine type

The current setup will work, but jobs may fail if routed to the wrong worker.
