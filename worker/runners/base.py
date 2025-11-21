from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class TranscriptionSegment(dict):
    """Segment with timestamp and word-level details."""
    
    def __init__(self, id: int, start: float, end: float, text: str, 
                 words: List[Dict[str, Any]] = None):
        super().__init__(
            id=id,
            start=start,
            end=end,
            text=text,
            words=words or []
        )

class TranscriptionResult(dict):
    """Unified transcription output format."""
    
    def __init__(self, text: str, segments: List[TranscriptionSegment], 
                 language: str, engine: str):
        super().__init__(
            text=text,
            segments=segments,
            language=language,
            engine=engine
        )

class BaseRunner(ABC):
    """Abstract runner for transcription engines."""
    
    def __init__(self, model: str = "base", device: str = "cuda"):
        self.model = model
        self.device = device
    
    @abstractmethod
    def run(self, audio_path: str, language: Optional[str] = None, 
            **kwargs) -> TranscriptionResult:
        """
        Execute transcription.
        
        Args:
            audio_path: Path to audio file
            language: Optional language code (e.g., 'en', 'fr')
            **kwargs: Engine-specific parameters
        
        Returns:
            TranscriptionResult with normalized format
        """
        pass
    
    def _validate_audio(self, audio_path: str) -> bool:
        """Validate audio file exists and is readable."""
        import os
        return os.path.exists(audio_path) and os.path.getsize(audio_path) > 0

