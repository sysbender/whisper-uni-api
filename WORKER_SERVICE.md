# RQ Worker Implementation

Background job processor for executing transcription tasks.

## Dependencies

```
rq==1.14.0
redis==5.0.0
pydantic==2.5.0
```

## Project Structure

```
worker/
├── main.py                # Worker setup and start
├── tasks.py               # Job task definitions
├── runners/
│   ├── base.py           # Abstract runner interface
│   ├── whisperx.py       # WhisperX implementation
│   └── timestamped.py    # whisper-timestamped implementation
├── config.py             # Configuration
└── tests/
    └── test_worker.py
```

## Core Architecture

### Base Runner Interface

```python
# worker/runners/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseRunner(ABC):
    """Abstract base for transcription engines."""
    
    def __init__(self, model: str = "base", device: str = "cuda"):
        self.model = model
        self.device = device
    
    @abstractmethod
    def run(self, audio_path: str, language: str = None, **kwargs) -> Dict[str, Any]:
        """
        Run transcription on audio file.
        
        Returns:
            {
                "text": "full transcription",
                "segments": [
                    {
                        "id": 0,
                        "start": 0.0,
                        "end": 2.5,
                        "text": "segment text",
                        "words": [
                            {"word": "hello", "start": 0.0, "end": 0.5}
                        ]
                    }
                ],
                "language": "en"
            }
        """
        pass
```

### WhisperX Runner

```python
# worker/runners/whisperx.py

import subprocess
import json
from .base import BaseRunner

class WhisperXRunner(BaseRunner):
    """WhisperX transcription engine."""
    
    def run(self, audio_path: str, language: str = None, **kwargs):
        """Execute WhisperX CLI and parse output."""
        
        cmd = [
            "whisperx",
            audio_path,
            "--model", self.model,
            "--device", self.device,
            "--output_format", "json",
            "--output_dir", "/tmp/whisperx_output"
        ]
        
        if language:
            cmd.extend(["--language", language])
        
        # Run CLI
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        
        if result.returncode != 0:
            raise RuntimeError(f"WhisperX failed: {result.stderr}")
        
        # Parse output JSON
        output_file = f"/tmp/whisperx_output/{audio_path.split('/')[-1]}.json"
        with open(output_file, 'r') as f:
            output = json.load(f)
        
        # Normalize to unified format
        return self._normalize(output)
    
    def _normalize(self, output: dict) -> dict:
        """Convert WhisperX output to unified format."""
        return {
            "text": output.get("text", ""),
            "segments": output.get("segments", []),
            "language": output.get("language", "unknown")
        }
```

### Whisper-Timestamped Runner

```python
# worker/runners/timestamped.py

import subprocess
import json
from .base import BaseRunner

class TimestampedRunner(BaseRunner):
    """whisper-timestamped transcription engine."""
    
    def run(self, audio_path: str, language: str = None, **kwargs):
        """Execute whisper-timestamped CLI and parse output."""
        
        cmd = [
            "whisper-timestamped",
            audio_path,
            "--model", self.model,
            "--device", self.device,
            "--output_format", "json",
            "--output_dir", "/tmp/timestamped_output"
        ]
        
        if language:
            cmd.extend(["--language", language])
        
        # Run CLI
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        
        if result.returncode != 0:
            raise RuntimeError(f"whisper-timestamped failed: {result.stderr}")
        
        # Parse output JSON
        output_file = f"/tmp/timestamped_output/{audio_path.split('/')[-1]}.json"
        with open(output_file, 'r') as f:
            output = json.load(f)
        
        # Normalize to unified format
        return self._normalize(output)
    
    def _normalize(self, output: dict) -> dict:
        """Convert timestamped output to unified format."""
        return {
            "text": output.get("text", ""),
            "segments": output.get("segments", []),
            "language": output.get("language", "unknown")
        }
```

## Task Definition

```python
# worker/tasks.py

from redis import Redis
from worker.runners.whisperx import WhisperXRunner
from worker.runners.timestamped import TimestampedRunner
from worker.config import Config
import os

redis_conn = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

def get_runner(engine: str, model: str = "base"):
    """Factory to get appropriate runner."""
    if engine == "whisperx":
        return WhisperXRunner(model=model, device="cuda")
    elif engine == "timestamped":
        return TimestampedRunner(model=model, device="cuda")
    else:
        raise ValueError(f"Unknown engine: {engine}")

def transcribe(job_id: str, audio_path: str, engine: str, 
               language: str = None, model: str = "base"):
    """
    Main transcription task.
    
    Args:
        job_id: Unique job identifier
        audio_path: Path to uploaded audio file
        engine: Engine to use (whisperx, timestamped)
        language: Optional language code
        model: Model size (base, small, medium, large)
    
    Returns:
        dict: Transcription result with segments and timestamps
    """
    
    try:
        # Validate audio file exists
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Get runner and execute
        runner = get_runner(engine, model)
        result = runner.run(audio_path, language=language)
        
        # Cleanup
        os.remove(audio_path)
        
        return result
    
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")
```

## Worker Startup

```python
# worker/main.py

from rq import Worker
from redis import Redis
from worker.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_worker():
    """Start RQ worker listening for jobs."""
    
    redis_conn = Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT
    )
    
    worker = Worker(['default'], connection=redis_conn)
    logger.info("Worker started, listening for jobs...")
    worker.work()

if __name__ == '__main__':
    start_worker()
```

## Test Cases

```python
# worker/tests/test_worker.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from worker.tasks import transcribe, get_runner
from worker.runners.whisperx import WhisperXRunner
from worker.runners.timestamped import TimestampedRunner
import json
import os

@pytest.fixture
def sample_audio(tmp_path):
    """Create dummy audio file."""
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"RIFF" + b"\x00" * 100)
    return str(audio_file)

@pytest.fixture
def mock_output():
    """Mock transcription output."""
    return {
        "text": "hello world",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 1.0,
                "text": "hello",
                "words": [{"word": "hello", "start": 0.0, "end": 1.0}]
            }
        ],
        "language": "en"
    }

def test_get_runner_whisperx():
    """Test runner factory for WhisperX."""
    runner = get_runner("whisperx", "base")
    assert isinstance(runner, WhisperXRunner)
    assert runner.model == "base"

def test_get_runner_timestamped():
    """Test runner factory for timestamped."""
    runner = get_runner("timestamped", "small")
    assert isinstance(runner, TimestampedRunner)
    assert runner.model == "small"

def test_get_runner_invalid():
    """Test runner factory with invalid engine."""
    with pytest.raises(ValueError):
        get_runner("invalid_engine")

@patch('worker.tasks.get_runner')
def test_transcribe_success(mock_get_runner, sample_audio, mock_output):
    """Test successful transcription."""
    
    # Mock runner
    mock_runner = Mock()
    mock_runner.run.return_value = mock_output
    mock_get_runner.return_value = mock_runner
    
    # Execute
    result = transcribe(
        "job-123",
        sample_audio,
        "whisperx",
        language="en",
        model="base"
    )
    
    assert result["text"] == "hello world"
    assert len(result["segments"]) == 1
    assert result["language"] == "en"
    mock_runner.run.assert_called_once()

@patch('worker.tasks.get_runner')
def test_transcribe_file_not_found(mock_get_runner):
    """Test transcription with missing file."""
    
    mock_runner = Mock()
    mock_get_runner.return_value = mock_runner
    
    with pytest.raises(FileNotFoundError):
        transcribe("job-123", "/nonexistent/file.wav", "whisperx")

@patch('subprocess.run')
def test_whisperx_runner_success(mock_subprocess, tmp_path, mock_output):
    """Test WhisperX runner execution."""
    
    # Create output file
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    output_file = output_dir / "test.wav.json"
    output_file.write_text(json.dumps(mock_output))
    
    # Mock subprocess
    mock_subprocess.return_value = Mock(returncode=0, stderr="")
    
    # Patch temp output dir
    with patch('worker.runners.whisperx.WhisperXRunner._normalize', return_value=mock_output):
        runner = WhisperXRunner()
        result = runner.run(str(tmp_path / "test.wav"), language="en")
    
    assert result["text"] == "hello world"

@patch('subprocess.run')
def test_whisperx_runner_failure(mock_subprocess, tmp_path):
    """Test WhisperX runner error handling."""
    
    mock_subprocess.return_value = Mock(
        returncode=1,
        stderr="Model not found"
    )
    
    runner = WhisperXRunner()
    
    with pytest.raises(RuntimeError, match="WhisperX failed"):
        runner.run(str(tmp_path / "test.wav"))

def test_timestamped_runner_normalize(mock_output):
    """Test timestamped runner output normalization."""
    
    runner = TimestampedRunner()
    normalized = runner._normalize(mock_output)
    
    assert normalized["text"] == "hello world"
    assert normalized["language"] == "en"
    assert len(normalized["segments"]) == 1
```

## Configuration

```python
# worker/config.py

import os

class Config:
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    WORKER_NAME = os.getenv("WORKER_NAME", "default")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

## Running

```bash
# Development
python -m worker.main

# With Docker
docker run --gpus all \
  -e REDIS_HOST=redis \
  -e REDIS_PORT=6379 \
  whisper-worker:latest
```
