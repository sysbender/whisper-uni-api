# worker/tests/test_worker_with_mock.py
from worker.tasks import transcribe

def test_transcribe_with_fixture(use_mock_runner, sample_audio):
    """Automatic mock injection via fixture."""
    # get_runner is automatically patched
    result = transcribe(
        "job-123",
        sample_audio,
        "whisperx",
        language="en"
    )
    
    assert result["engine"] == "mock"
    assert len(result["segments"]) > 0