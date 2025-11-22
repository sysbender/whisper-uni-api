# worker/tests/test_worker_with_mock.py
import pytest
from tests.mock.runner import MockWhisperRunner
from worker.tasks import transcribe
import os


def test_transcribe_with_direct_mock(sample_audio):
    """Use mock runner directly without patching."""
    runner = MockWhisperRunner()
    result = runner.run(sample_audio, language="en")
    
    assert result["engine"] == "mock"
    assert "mock transcription" in result["text"].lower()


def test_transcribe_with_patched_runner(sample_audio):
    """Patch get_runner to use mock."""
    from unittest.mock import patch
    from tests.mock.runner import MockWhisperRunner
    
    with patch("worker.tasks.get_runner") as mock_get:
        mock_get.return_value = MockWhisperRunner()
        
        # Now transcribe will use mock runner
        result = transcribe(
            "job-123",
            sample_audio,
            "whisperx",  # Engine name doesn't matter, mock is returned
            language="en"
        )
        
        assert result["engine"] == "mock"
        mock_get.assert_called_once_with("whisperx", "base")