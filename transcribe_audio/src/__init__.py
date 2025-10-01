"""
Audio Transcription Package

A modular package for transcribing audio files using OpenAI's Whisper API
with optional language detection capabilities.

Main modules:
- core: Business logic for transcription and language detection
- cli: Command-line interface
- config: Configuration management

Usage:
    # As a library
    from transcribe_audio.core import transcribe_audio
    result = transcribe_audio("audio.mp3")
    
    # As CLI
    python -m transcribe_audio.cli.transcribe_cli audio.mp3
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

