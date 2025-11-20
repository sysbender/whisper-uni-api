# Engine Runners Implementation

Abstraction layer for different Whisper-based transcription engines.

## Overview

Unified interface for multiple transcription engines with normalized output format.

## Base Runner Interface

```python
# runners/base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class TranscriptionSegment(dict):
    """Segment with timestamp and word-level details."""
    
    def __init__(self, id: int, start: float, end: float, text: str, 
                 words: List[Dict[str, float]] = None):
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
```

## WhisperX Runner

```python
# runners/whisperx.py

import subprocess
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from .base import BaseRunner, TranscriptionSegment, TranscriptionResult

class WhisperXRunner(BaseRunner):
    """WhisperX with alignment and diarization support."""
    
    def run(self, audio_path: str, language: Optional[str] = None, 
            diarize: bool = False, **kwargs) -> TranscriptionResult:
        """
        Execute WhisperX transcription.
        
        Args:
            audio_path: Path to audio file
            language: Language code (optional)
            diarize: Enable speaker diarization
            **kwargs: Additional CLI arguments
        
        Returns:
            Normalized transcription result
        """
        
        if not self._validate_audio(audio_path):
            raise FileNotFoundError(f"Invalid audio: {audio_path}")
        
        # Prepare output directory
        output_dir = Path("/tmp/whisperx_output")
        output_dir.mkdir(exist_ok=True)
        
        # Build CLI command
        cmd = [
            "whisperx",
            audio_path,
            "--model", self.model,
            "--device", self.device,
            "--output_format", "json",
            "--output_dir", str(output_dir),
            "--align_model", "wav2vec2_align_multilingual_v1",
            "--compute_type", "float16" if self.device == "cuda" else "int8"
        ]
        
        if language:
            cmd.extend(["--language", language])
        
        if diarize:
            cmd.append("--diarize_model")
            cmd.append("pyannote/speaker-diarization-3.1")
        
        # Execute
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,
                check=False
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"WhisperX error: {result.stderr}")
            
        except subprocess.TimeoutExpired:
            raise TimeoutError("WhisperX processing exceeded 1 hour")
        
        # Parse JSON output
        audio_name = Path(audio_path).stem
        output_file = output_dir / f"{audio_name}.json"
        
        if not output_file.exists():
            raise RuntimeError(f"Output file not generated: {output_file}")
        
        with open(output_file, 'r') as f:
            raw_output = json.load(f)
        
        return self._normalize(raw_output, audio_path)
    
    def _normalize(self, output: Dict[str, Any], audio_path: str) -> TranscriptionResult:
        """Convert WhisperX output to unified format."""
        
        segments = []
        for seg in output.get("segments", []):
            # Extract word-level timestamps
            words = []
            for word_info in seg.get("words", []):
                words.append({
                    "word": word_info.get("word", ""),
                    "start": float(word_info.get("start", 0)),
                    "end": float(word_info.get("end", 0))
                })
            
            segment = TranscriptionSegment(
                id=seg.get("id", 0),
                start=float(seg.get("start", 0)),
                end=float(seg.get("end", 0)),
                text=seg.get("text", "").strip(),
                words=words
            )
            segments.append(segment)
        
        full_text = output.get("text", "").strip()
        if not full_text:
            full_text = " ".join(s["text"] for s in segments)
        
        return TranscriptionResult(
            text=full_text,
            segments=segments,
            language=output.get("language", "unknown"),
            engine="whisperx"
        )
```

## Whisper-Timestamped Runner

```python
# runners/timestamped.py

import subprocess
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from .base import BaseRunner, TranscriptionSegment, TranscriptionResult

class TimestampedRunner(BaseRunner):
    """whisper-timestamped - lightweight timestamped transcription."""
    
    def run(self, audio_path: str, language: Optional[str] = None, 
            vad_filter: bool = True, **kwargs) -> TranscriptionResult:
        """
        Execute whisper-timestamped transcription.
        
        Args:
            audio_path: Path to audio file
            language: Language code (optional)
            vad_filter: Enable voice activity detection
            **kwargs: Additional CLI arguments
        
        Returns:
            Normalized transcription result
        """
        
        if not self._validate_audio(audio_path):
            raise FileNotFoundError(f"Invalid audio: {audio_path}")
        
        # Prepare output directory
        output_dir = Path("/tmp/timestamped_output")
        output_dir.mkdir(exist_ok=True)
        
        # Build CLI command
        cmd = [
            "whisper-timestamped",
            audio_path,
            "--model", self.model,
            "--device", self.device,
            "--output_format", "json",
            "--output_dir", str(output_dir)
        ]
        
        if language:
            cmd.extend(["--language", language])
        
        if not vad_filter:
            cmd.append("--no_vad")
        
        # Execute
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,
                check=False
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"whisper-timestamped error: {result.stderr}")
            
        except subprocess.TimeoutExpired:
            raise TimeoutError("Processing exceeded 1 hour")
        
        # Parse JSON output
        audio_name = Path(audio_path).stem
        output_file = output_dir / f"{audio_name}.json"
        
        if not output_file.exists():
            raise RuntimeError(f"Output file not generated: {output_file}")
        
        with open(output_file, 'r') as f:
            raw_output = json.load(f)
        
        return self._normalize(raw_output, audio_path)
    
    def _normalize(self, output: Dict[str, Any], audio_path: str) -> TranscriptionResult:
        """Convert whisper-timestamped output to unified format."""
        
        segments = []
        for seg in output.get("segments", []):
            # Extract word-level timestamps if available
            words = []
            if "words" in seg:
                for word_info in seg["words"]:
                    words.append({
                        "word": word_info.get("word", ""),
                        "start": float(word_info.get("start", 0)),
                        "end": float(word_info.get("end", 0))
                    })
            
            segment = TranscriptionSegment(
                id=seg.get("id", 0),
                start=float(seg.get("start", 0)),
                end=float(seg.get("end", 0)),
                text=seg.get("text", "").strip(),
                words=words
            )
            segments.append(segment)
        
        full_text = output.get("text", "").strip()
        if not full_text:
            full_text = " ".join(s["text"] for s in segments)
        
        return TranscriptionResult(
            text=full_text,
            segments=segments,
            language=output.get("language", "unknown"),
            engine="timestamped"
        )
```

## Test Cases

```python
# runners/tests/test_runners.py

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from runners.whisperx import WhisperXRunner
from runners.timestamped import TimestampedRunner
from runners.base import TranscriptionSegment, TranscriptionResult

@pytest.fixture
def sample_audio(tmp_path):
    """Create dummy audio file."""
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"RIFF" + b"\x00" * 1000)
    return str(audio_file)

@pytest.fixture
def whisperx_output():
    """Mock WhisperX output."""
    return {
        "text": "hello world this is a test",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 1.5,
                "text": "hello world",
                "words": [
                    {"word": "hello", "start": 0.0, "end": 0.5},
                    {"word": "world", "start": 0.6, "end": 1.5}
                ]
            }
        ],
        "language": "en"
    }

@pytest.fixture
def timestamped_output():
    """Mock whisper-timestamped output."""
    return {
        "text": "hello world",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "hello world",
                "words": [
                    {"word": "hello", "start": 0.0, "end": 1.0},
                    {"word": "world", "start": 1.1, "end": 2.0}
                ]
            }
        ],
        "language": "en"
    }

def test_transcription_segment_creation():
    """Test segment data structure."""
    seg = TranscriptionSegment(
        id=0,
        start=0.0,
        end=1.5,
        text="hello",
        words=[{"word": "hello", "start": 0.0, "end": 1.5}]
    )
    
    assert seg["id"] == 0
    assert seg["start"] == 0.0
    assert seg["end"] == 1.5
    assert seg["text"] == "hello"
    assert len(seg["words"]) == 1

def test_transcription_result_creation(whisperx_output):
    """Test result data structure."""
    segments = [
        TranscriptionSegment(
            id=0, start=0.0, end=1.5,
            text="hello world",
            words=[{"word": "hello", "start": 0.0, "end": 1.5}]
        )
    ]
    
    result = TranscriptionResult(
        text="hello world",
        segments=segments,
        language="en",
        engine="whisperx"
    )
    
    assert result["text"] == "hello world"
    assert result["engine"] == "whisperx"
    assert len(result["segments"]) == 1

@patch('subprocess.run')
def test_whisperx_runner_success(mock_subprocess, tmp_path, sample_audio, whisperx_output):
    """Test WhisperX runner successful execution."""
    
    # Create output file
    output_dir = Path("/tmp/whisperx_output")
    output_dir.mkdir(exist_ok=True)
    audio_name = Path(sample_audio).stem
    output_file = output_dir / f"{audio_name}.json"
    output_file.write_text(json.dumps(whisperx_output))
    
    # Mock subprocess
    mock_subprocess.return_value = Mock(returncode=0, stderr="")
    
    runner = WhisperXRunner(model="base")
    result = runner.run(sample_audio, language="en")
    
    assert result["text"] == "hello world this is a test"
    assert result["engine"] == "whisperx"
    assert result["language"] == "en"
    assert len(result["segments"]) == 1
    assert result["segments"][0]["words"][0]["word"] == "hello"

@patch('subprocess.run')
def test_whisperx_runner_with_diarization(mock_subprocess, tmp_path, sample_audio, whisperx_output):
    """Test WhisperX runner with diarization enabled."""
    
    # Create output file
    output_dir = Path("/tmp/whisperx_output")
    output_dir.mkdir(exist_ok=True)
    audio_name = Path(sample_audio).stem
    output_file = output_dir / f"{audio_name}.json"
    output_file.write_text(json.dumps(whisperx_output))
    
    mock_subprocess.return_value = Mock(returncode=0, stderr="")
    
    runner = WhisperXRunner(model="base")
    result = runner.run(sample_audio, language="en", diarize=True)
    
    # Verify diarize flag was passed
    call_args = mock_subprocess.call_args[0][0]
    assert "--diarize_model" in call_args
    
    assert result["text"] == "hello world this is a test"

def test_whisperx_runner_invalid_audio():
    """Test WhisperX runner with invalid audio."""
    runner = WhisperXRunner()
    
    with pytest.raises(FileNotFoundError):
        runner.run("/nonexistent/audio.wav")

@patch('subprocess.run')
def test_whisperx_runner_subprocess_error(mock_subprocess, sample_audio):
    """Test WhisperX runner CLI error handling."""
    
    mock_subprocess.return_value = Mock(
        returncode=1,
        stderr="CUDA error"
    )
    
    runner = WhisperXRunner()
    
    with pytest.raises(RuntimeError, match="WhisperX error"):
        runner.run(sample_audio)

@patch('subprocess.run')
def test_timestamped_runner_success(mock_subprocess, tmp_path, sample_audio, timestamped_output):
    """Test timestamped runner successful execution."""
    
    # Create output file
    output_dir = Path("/tmp/timestamped_output")
    output_dir.mkdir(exist_ok=True)
    audio_name = Path(sample_audio).stem
    output_file = output_dir / f"{audio_name}.json"
    output_file.write_text(json.dumps(timestamped_output))
    
    mock_subprocess.return_value = Mock(returncode=0, stderr="")
    
    runner = TimestampedRunner(model="small")
    result = runner.run(sample_audio, language="en")
    
    assert result["text"] == "hello world"
    assert result["engine"] == "timestamped"
    assert len(result["segments"]) == 1

@patch('subprocess.run')
def test_timestamped_runner_vad_disabled(mock_subprocess, sample_audio, timestamped_output):
    """Test timestamped runner with VAD disabled."""
    
    output_dir = Path("/tmp/timestamped_output")
    output_dir.mkdir(exist_ok=True)
    audio_name = Path(sample_audio).stem
    output_file = output_dir / f"{audio_name}.json"
    output_file.write_text(json.dumps(timestamped_output))
    
    mock_subprocess.return_value = Mock(returncode=0, stderr="")
    
    runner = TimestampedRunner()
    result = runner.run(sample_audio, vad_filter=False)
    
    # Verify no_vad flag was passed
    call_args = mock_subprocess.call_args[0][0]
    assert "--no_vad" in call_args

def test_whisperx_normalize_empty_segments():
    """Test normalization with empty segments."""
    runner = WhisperXRunner()
    
    output = {
        "text": "",
        "segments": [],
        "language": "en"
    }
    
    result = runner._normalize(output, "/fake/audio.wav")
    
    assert result["text"] == ""
    assert len(result["segments"]) == 0
    assert result["language"] == "en"

def test_timestamped_normalize_no_words():
    """Test normalization without word-level timestamps."""
    runner = TimestampedRunner()
    
    output = {
        "text": "hello world",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.0,
                "text": "hello world"
            }
        ],
        "language": "en"
    }
    
    result = runner._normalize(output, "/fake/audio.wav")
    
    assert len(result["segments"]) == 1
    assert result["segments"][0]["words"] == []
```

## Configuration

```python
# runners/config.py

class RunnerConfig:
    # Model sizes
    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large"]
    
    # Device options
    DEVICES = ["cuda", "cpu"]
    
    # Timeouts (seconds)
    TRANSCRIPTION_TIMEOUT = 3600
    
    # Output format
    UNIFIED_FORMAT_VERSION = "1.0"
```
