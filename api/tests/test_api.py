import pytest
from fastapi.testclient import TestClient
from api.handlers import app
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

client = TestClient(app)

@pytest.fixture
def sample_audio(tmp_path):
    """Create dummy audio file."""
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"RIFF" + b"\x00" * 100)  # Minimal WAV header
    return audio_file

@pytest.fixture
def mock_redis_queue():
    """Mock Redis queue."""
    with patch('api.handlers.redis_conn') as mock_redis, \
         patch('api.handlers.q') as mock_queue:
        mock_job = MagicMock()
        mock_job.get_status.return_value = "queued"
        mock_job.result = None
        mock_job.exc_info = None
        mock_queue.fetch_job.return_value = mock_job
        mock_queue.enqueue.return_value = mock_job
        yield mock_queue

def test_health_check():
    """Test health endpoint."""
    with patch('api.handlers.redis_conn') as mock_redis:
        mock_redis.ping.return_value = True
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

def test_transcribe_success(sample_audio, mock_redis_queue):
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

def test_transcribe_invalid_format(tmp_path, mock_redis_queue):
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

def test_transcribe_invalid_engine(sample_audio, mock_redis_queue):
    """Test invalid engine parameter."""
    with open(sample_audio, "rb") as f:
        response = client.post(
            "/transcribe",
            files={"file": ("test.wav", f, "audio/wav")},
            data={"engine": "invalid_engine"}
        )
    
    assert response.status_code == 422  # Validation error

def test_get_job_status_not_found(mock_redis_queue):
    """Test querying non-existent job."""
    mock_redis_queue.fetch_job.return_value = None
    response = client.get("/status/nonexistent-job-id")
    assert response.status_code == 404

def test_get_job_status_exists(sample_audio, mock_redis_queue):
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

