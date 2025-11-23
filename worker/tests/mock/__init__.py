"""
Isolated mock Whisper package for testing.
Completely separate from production worker/runners code.
"""
from .runner import MockWhisperRunner

__all__ = ["MockWhisperRunner"]