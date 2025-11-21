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
        output_dir.mkdir(exist_ok=True, parents=True)
        
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

