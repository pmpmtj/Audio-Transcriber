"""
Audio Transcription Package Entry Point

This package provides audio transcription functionality with language detection.
"""

from .src import transcribe_audio, TranscriptionConfig

__all__ = ['transcribe_audio', 'TranscriptionConfig']

