"""
Test-only factory helper for injecting mock runner into tests.
Does not modify production worker.tasks.get_runner.
"""
from .runner import MockWhisperRunner
from worker.runners.whisperx import WhisperXRunner
from worker.runners.timestamped import TimestampedRunner
from typing import Union


def get_test_runner(engine: str, model: str = "base", use_mock: bool = False):
    """
    Test-only factory that can return mock or real runners.
    
    Args:
        engine: Engine name (whisperx, timestamped, mock)
        model: Model size
        use_mock: If True, returns MockWhisperRunner regardless of engine
    
    Returns:
        Runner instance
        
    Raises:
        ValueError: If engine is not supported
    """
    if use_mock or engine == "mock":
        return MockWhisperRunner(model=model, device="cpu")
    
    if engine == "whisperx":
        return WhisperXRunner(model=model, device="cuda")
    elif engine == "timestamped":
        return TimestampedRunner(model=model, device="cuda")
    else:
        raise ValueError(f"Unknown engine: {engine}")