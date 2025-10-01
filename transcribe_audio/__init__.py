"""
Audio Transcription Package Entry Point

This package provides audio transcription functionality with language detection.
"""

from .core import transcribe_audio, detect_language_from_text, detect_language_with_probe
from .config import TranscriptionConfig

__version__ = "1.0.0"
__all__ = [
    'transcribe_audio',
    'detect_language_from_text', 
    'detect_language_with_probe',
    'TranscriptionConfig'
]

