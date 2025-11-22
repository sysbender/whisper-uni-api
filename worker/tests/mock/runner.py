"""
Isolated mock Whisper runner for testing.
This package is completely separate from production code.
"""
from pathlib import Path
from typing import Optional, Dict, Any
from worker.runners.base import BaseRunner, TranscriptionSegment, TranscriptionResult


class MockWhisperRunner(BaseRunner):
    """
    Mock Whisper runner for testing.
    
    Implements the BaseRunner interface but doesn't require
    any external Whisper dependencies or GPU. Returns predictable
    mock transcription data instantly.
    """
    
    def __init__(self, model: str = "base", device: str = "cpu"):
        """
        Initialize mock runner.
        
        Args:
            model: Model name (ignored in mock, kept for interface compatibility)
            device: Device (always uses CPU in mock)
        """
        # Override device to always be CPU for mock
        super().__init__(model=model, device="cpu")
    
    def run(self, audio_path: str, language: Optional[str] = None, 
            **kwargs) -> TranscriptionResult:
        """
        Execute mock transcription (instant, no actual processing).
        
        Args:
            audio_path: Path to audio file
            language: Optional language code (defaults to 'en' if not provided)
            **kwargs: Additional parameters (ignored in mock)
        
        Returns:
            Normalized transcription result with mock data
        
        Raises:
            FileNotFoundError: If audio file doesn't exist
        """
        
        if not self._validate_audio(audio_path):
            raise FileNotFoundError(f"Invalid audio: {audio_path}")
        
        # Generate mock transcription based on filename
        audio_name = Path(audio_path).stem
        detected_language = language or "en"
        
        # Create realistic mock segments with word-level timestamps
        segments = [
            TranscriptionSegment(
                id=0,
                start=0.0,
                end=2.5,
                text="This is a mock transcription",
                words=[
                    {"word": "This", "start": 0.0, "end": 0.4},
                    {"word": "is", "start": 0.5, "end": 0.7},
                    {"word": "a", "start": 0.8, "end": 0.9},
                    {"word": "mock", "start": 1.0, "end": 1.3},
                    {"word": "transcription", "start": 1.4, "end": 2.5}
                ]
            ),
            TranscriptionSegment(
                id=1,
                start=2.5,
                end=5.0,
                text=f"from the file {audio_name}",
                words=[
                    {"word": "from", "start": 2.5, "end": 2.8},
                    {"word": "the", "start": 2.9, "end": 3.0},
                    {"word": "file", "start": 3.1, "end": 3.4},
                    {"word": audio_name, "start": 3.5, "end": 4.5}
                ]
            )
        ]
        
        full_text = "This is a mock transcription from the file " + audio_name
        
        return TranscriptionResult(
            text=full_text,
            segments=segments,
            language=detected_language,
            engine="mock"
        )