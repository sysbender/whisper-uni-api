# FastAPI Service Implementation

Core REST API for receiving audio uploads and job status queries.

## Dependencies

```
fastapi==0.104.1
python-multipart==0.0.6
redis==5.0.0
rq==1.14.0
pydantic==2.5.0
```

## Project Structure

```
api/
├── main.py                 # FastAPI app initialization
├── models.py              # Pydantic schemas
├── handlers.py            # Endpoint logic
├── storage.py             # File management
└── tests/
    └── test_api.py
```

## Core Models

```python
# models.py

from pydantic import BaseModel, Field
from typing import Optional

class TranscribeRequest(BaseModel):
    engine: str = Field(..., regex="^(whisperx|timestamped)$")
    language: Optional[str] = None
    model: Optional[str] = None

class TranscribeResponse(BaseModel):
    job_id: str
    status: str = "queued"

class JobStatus(BaseModel):
    job_id: str
    status: str  # queued, started, finished, failed
    result: Optional[dict] = None
    error: Optional[str] = None
```

## Endpoints

### POST /transcribe

Accept audio file and enqueue transcription job.

```python
# handlers.py

from fastapi import FastAPI, UploadFile, File, Form
from rq import Queue
from redis import Redis
import uuid
import os

app = FastAPI()
redis_conn = Redis(host='redis', port=6379)
q = Queue(connection=redis_conn)

UPLOAD_DIR = "/tmp/uploads"
ALLOWED_FORMATS = {'mp3', 'wav', 'm4a', 'flac'}

@app.post("/transcribe", response_model=TranscribeResponse)
async def upload_and_transcribe(
    file: UploadFile = File(...),
    engine: str = Form(...),
    language: Optional[str] = Form(None),
    model: Optional[str] = Form(None)
):
    """Upload audio and enqueue transcription job."""
    
    # Validate file format
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ALLOWED_FORMATS:
        raise HTTPException(400, "Unsupported format")
    
    # Save file
    job_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{job_id}.{file_ext}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        if len(content) > 500 * 1024 * 1024:  # 500MB limit
            raise HTTPException(400, "File too large")
        f.write(content)
    
    # Enqueue job
    q.enqueue(
        'worker.tasks.transcribe',
        job_id,
        file_path,
        engine,
        language=language,
        model=model,
        job_id=job_id
    )
    
    return TranscribeResponse(job_id=job_id)

@app.get("/status/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    """Query job status and retrieve results."""
    
    job = q.fetch_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    return JobStatus(
        job_id=job_id,
        status=job.get_status(),
        result=job.result,
        error=job.exc_info
    )

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
```

## Test Cases

```python
# tests/test_api.py

import pytest
from fastapi.testclient import TestClient
from api.main import app
import os
from pathlib import Path

client = TestClient(app)

@pytest.fixture
def sample_audio(tmp_path):
    """Create dummy audio file."""
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"RIFF" + b"\x00" * 100)  # Minimal WAV header
    return audio_file

def test_health_check():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_transcribe_success(sample_audio):
    """Test successful audio upload and job enqueue."""
    with open(sample_audio, "rb") as f:
        response = client.post(
            "/transcribe",
            files={"file": ("test.wav", f, "audio/wav")},
            data={"engine": "whisperx", "language": "en"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"

def test_transcribe_invalid_format(tmp_path):
    """Test rejection of unsupported format."""
    invalid_file = tmp_path / "test.txt"
    invalid_file.write_text("not audio")
    
    with open(invalid_file, "rb") as f:
        response = client.post(
            "/transcribe",
            files={"file": ("test.txt", f)},
            data={"engine": "whisperx"}
        )
    
    assert response.status_code == 400

def test_transcribe_invalid_engine(sample_audio):
    """Test invalid engine parameter."""
    with open(sample_audio, "rb") as f:
        response = client.post(
            "/transcribe",
            files={"file": ("test.wav", f, "audio/wav")},
            data={"engine": "invalid_engine"}
        )
    
    assert response.status_code == 422  # Validation error

def test_get_job_status_not_found():
    """Test querying non-existent job."""
    response = client.get("/status/nonexistent-job-id")
    assert response.status_code == 404

def test_get_job_status_exists(sample_audio):
    """Test querying existing job."""
    # First, upload a file
    with open(sample_audio, "rb") as f:
        upload_response = client.post(
            "/transcribe",
            files={"file": ("test.wav", f, "audio/wav")},
            data={"engine": "timestamped"}
        )
    
    job_id = upload_response.json()["job_id"]
    
    # Query status
    status_response = client.get(f"/status/{job_id}")
    assert status_response.status_code == 200
    assert status_response.json()["job_id"] == job_id
    assert status_response.json()["status"] in ["queued", "started"]
```

## Configuration

```python
# config.py

import os

class Config:
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/uploads")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 500 * 1024 * 1024))  # 500MB
    ALLOWED_FORMATS = {"mp3", "wav", "m4a", "flac"}
```

## Running

```bash
# Development
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app --bind 0.0.0.0:8000
```
