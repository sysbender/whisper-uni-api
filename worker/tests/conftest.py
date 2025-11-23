"""
Pytest configuration and shared fixtures for tests.
"""
import pytest
from unittest.mock import patch
from tests.mock.runner import MockWhisperRunner


@pytest.fixture
def sample_audio(tmp_path):
    """Create dummy audio file for testing."""
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"RIFF" + b"\x00" * 100)
    return str(audio_file)


@pytest.fixture
def mock_runner():
    """Fixture providing a MockWhisperRunner instance."""
    return MockWhisperRunner(model="base", device="cpu")


@pytest.fixture
def use_mock_runner(monkeypatch):
    """
    Fixture that patches worker.tasks.get_runner to return MockWhisperRunner.
    
    Usage in tests:
        def test_something(use_mock_runner):
            # Now get_runner will return MockWhisperRunner
            result = transcribe(...)
    """
    original_get_runner = __import__("worker.tasks", fromlist=["get_runner"]).get_runner
    
    def mock_get_runner(engine: str, model: str = "base"):
        """Return MockWhisperRunner for any engine during tests."""
        return MockWhisperRunner(model=model, device="cpu")
    
    monkeypatch.setattr("worker.tasks.get_runner", mock_get_runner)
    yield
    
    # Cleanup happens automatically with monkeypatch


@pytest.fixture
def use_mock_runner_for_engine():
    """
    Context manager to temporarily use mock runner for specific tests.
    
    Usage:
        def test_something():
            with use_mock_runner_for_engine():
                result = transcribe(..., engine="whisperx")  # Will use mock
    """
    from contextlib import contextmanager
    
    @contextmanager
    def _mock_context():
        with patch("worker.tasks.get_runner") as mock_get:
            mock_get.return_value = MockWhisperRunner()
            yield mock_get
    
    return _mock_context()