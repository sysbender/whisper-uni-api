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
        "language": "en",
        "engine": "whisperx"
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
    output_dir = tmp_path / "whisperx_output"
    output_dir.mkdir()
    output_file = output_dir / "test.json"
    output_file.write_text(json.dumps(mock_output))
    
    # Mock subprocess
    mock_subprocess.return_value = Mock(returncode=0, stderr="")
    
    # Patch output path
    with patch('worker.runners.whisperx.Path') as mock_path:
        mock_path.return_value.mkdir = Mock()
        mock_path.return_value.__truediv__ = lambda x, y: output_file
        mock_path.return_value.exists.return_value = True
        
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
    
    with pytest.raises(RuntimeError, match="WhisperX error"):
        runner.run(str(tmp_path / "test.wav"))

def test_timestamped_runner_normalize(mock_output):
    """Test timestamped runner output normalization."""
    
    runner = TimestampedRunner()
    normalized = runner._normalize(mock_output, "/fake/audio.wav")
    
    assert normalized["text"] == "hello world"
    assert normalized["language"] == "en"
    assert len(normalized["segments"]) == 1

