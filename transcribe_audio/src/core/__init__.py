"""
Core business logic module for audio transcription.

This module provides the main transcription functionality that can be used
by different interfaces (CLI, web API, batch processing, etc.).
"""

from .transcription import transcribe_audio
from .language_detection import detect_language_from_text, detect_language_with_probe

__all__ = [
    'transcribe_audio',
    'detect_language_from_text', 
    'detect_language_with_probe'
]
