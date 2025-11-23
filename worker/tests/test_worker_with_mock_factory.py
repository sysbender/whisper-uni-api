# worker/tests/test_worker_with_mock.py
from tests.mock.factory import get_test_runner
from tests.mock.runner import MockWhisperRunner

def test_with_test_factory(sample_audio):
    """Use test factory helper."""
    runner = get_test_runner("whisperx", use_mock=True)
    assert isinstance(runner, MockWhisperRunner)
    
    result = runner.run(sample_audio)
    assert result["engine"] == "mock"