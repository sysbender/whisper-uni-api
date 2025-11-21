# Universal Whisper Transcription API

REST API for audio transcription using multiple Whisper-based engines (WhisperX and whisper-timestamped).

## Features

- **Multiple Engines**: Support for WhisperX (with alignment, diarization) and whisper-timestamped
- **Background Processing**: Asynchronous job processing with Redis Queue (RQ)
- **GPU Support**: GPU acceleration for transcription workers
- **Unified Output**: Normalized JSON format with word and segment-level timestamps
- **RESTful API**: FastAPI-based REST endpoints

## Architecture

```
┌─────────────┐              POST /transcribe              ┌──────────────┐
│   FastAPI   │ ──────────────────────────────────────→ │  Redis Queue │
│    (API)    │ ←───────────────────────────────────── │    (RQ)      │
└─────────────┘              job_id                        └──────────────┘
      ▲                                                            │
      │                        GET /status/{job_id}               │
      └────────────────────────────────────────────  dequeued  ───┘
                                                           │
                                                           ▼
                                              ┌──────────────────────┐
                                              │   RQ Worker (GPU)    │
                                              │ - WhisperX runner    │
                                              │ - timestamped runner │
                                              └──────────────────────┘
```

## Project Structure

```
whisper-uni-api/
├── api/                    # FastAPI service
│   ├── main.py            # FastAPI app initialization
│   ├── models.py          # Pydantic schemas
│   ├── handlers.py        # Endpoint logic
│   ├── storage.py         # File management
│   ├── config.py          # Configuration
│   └── tests/             # API tests
├── worker/                 # RQ background worker
│   ├── main.py            # Worker startup
│   ├── tasks.py           # Job task definitions
│   ├── config.py          # Configuration
│   ├── runners/           # Engine runners
│   │   ├── base.py        # Abstract runner interface
│   │   ├── whisperx.py    # WhisperX implementation
│   │   └── timestamped.py # whisper-timestamped implementation
│   └── tests/             # Worker tests
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile.api         # API service Dockerfile
├── Dockerfile.worker      # Worker service Dockerfile
└── README.md             # This file
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- NVIDIA Docker runtime (for GPU support)
- Python 3.11+ (for local development)

### Using Docker Compose

1. Clone the repository:
```bash
git clone <repository-url>
cd whisper-uni-api
```

2. Start services:
```bash
docker-compose up -d
```

3. Check service status:
```bash
docker-compose ps
```

4. View logs:
```bash
docker-compose logs -f api
docker-compose logs -f worker
```

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start Redis (using Docker):
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

3. Start API service:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

4. Start worker (in another terminal):
```bash
python -m worker.main
```

## API Endpoints

### POST /transcribe

Upload audio file and enqueue transcription job.

**Request:**
- `file`: Audio file (mp3, wav, m4a, flac)
- `engine`: Transcription engine (`whisperx` or `timestamped`)
- `language`: (Optional) Language code (e.g., `en`, `fr`)
- `model`: (Optional) Model size (`base`, `small`, `medium`, `large`)

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "queued"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -F "file=@audio.wav" \
  -F "engine=whisperx" \
  -F "language=en"
```

### GET /status/{job_id}

Query job status and retrieve results.

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "finished",
  "result": {
    "text": "Full transcription text",
    "segments": [
      {
        "id": 0,
        "start": 0.0,
        "end": 2.5,
        "text": "Segment text",
        "words": [
          {"word": "hello", "start": 0.0, "end": 0.5}
        ]
      }
    ],
    "language": "en",
    "engine": "whisperx"
  },
  "error": null
}
```

**Status values:**
- `queued`: Job is waiting in queue
- `started`: Job is being processed
- `finished`: Job completed successfully
- `failed`: Job failed with error

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "redis": "connected"
}
```

## Configuration

Environment variables (see `.env.example`):

- `REDIS_HOST`: Redis host (default: `redis`)
- `REDIS_PORT`: Redis port (default: `6379`)
- `UPLOAD_DIR`: Directory for uploaded files (default: `/tmp/uploads`)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: `524288000` = 500MB)
- `WORKER_NAME`: Worker name identifier (default: `worker-1`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Testing

Run tests:

```bash
# API tests
pytest api/tests/

# Worker tests
pytest worker/tests/

# All tests
pytest
```

## Engine Installation

The Docker images include placeholders for WhisperX and whisper-timestamped. To use them, you need to:

1. **WhisperX**:
```bash
pip install whisperx
```

2. **whisper-timestamped**:
```bash
pip install whisper-timestamped
```

Or uncomment the installation lines in `Dockerfile.worker`.

## Output Format

All engines return a unified JSON format:

```json
{
  "text": "Full transcription text",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 2.5,
      "text": "Segment text",
      "words": [
        {
          "word": "hello",
          "start": 0.0,
          "end": 0.5
        }
      ]
    }
  ],
  "language": "en",
  "engine": "whisperx"
}
```

## Deployment

### Production Considerations

1. **Multiple Workers**: Scale workers for multiple GPUs:
```yaml
worker-1:
  # ... configuration
worker-2:
  # ... configuration
```

2. **Gunicorn**: Use Gunicorn for production API:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app --bind 0.0.0.0:8000
```

3. **Monitoring**: Consider adding rq-dashboard for job monitoring:
```yaml
rq-dashboard:
  image: eoranged/rq-dashboard
  ports:
    - "9181:9181"
  environment:
    - RQ_DASHBOARD_REDIS_URL=redis://redis:6379
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

