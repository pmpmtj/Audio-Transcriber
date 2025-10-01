"""
Pytest configuration and shared fixtures.

This module provides common fixtures and configuration for all tests.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest


# ============================================================================
# Path and File Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_audio_path(temp_dir):
    """Create a fake audio file path for testing."""
    audio_file = temp_dir / "test_audio.mp3"
    audio_file.write_text("fake audio content")
    return audio_file


@pytest.fixture
def sample_m4a_path(temp_dir):
    """Create a fake M4A audio file path for testing."""
    audio_file = temp_dir / "test_audio.m4a"
    audio_file.write_text("fake m4a content")
    return audio_file


@pytest.fixture
def sample_wav_path(temp_dir):
    """Create a fake WAV audio file path for testing."""
    audio_file = temp_dir / "test_audio.wav"
    audio_file.write_text("fake wav content")
    return audio_file


@pytest.fixture
def nonexistent_audio_path(temp_dir):
    """Return a path to a non-existent audio file."""
    return temp_dir / "nonexistent.mp3"


# ============================================================================
# OpenAI Client Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    client = MagicMock()
    
    # Mock audio transcriptions
    client.audio.transcriptions.create = MagicMock()
    
    return client


@pytest.fixture
def mock_transcription_response():
    """Create a mock transcription response."""
    response = Mock()
    response.text = "This is a test transcription"
    response.model_dump = Mock(return_value={
        "text": "This is a test transcription",
        "language": "en",
    })
    return response


@pytest.fixture
def mock_transcription_response_json():
    """Create a mock transcription response in JSON format."""
    return {
        "text": "This is a test transcription",
        "language": "en",
        "duration": 10.5,
        "segments": []
    }


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture
def mock_api_key(monkeypatch):
    """Set a fake OpenAI API key for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key-for-testing")
    return "sk-test-fake-key-for-testing"


@pytest.fixture
def no_api_key(monkeypatch):
    """Remove OpenAI API key from environment."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


# ============================================================================
# Argument Fixtures (for CLI testing)
# ============================================================================

@pytest.fixture
def basic_cli_args():
    """Create basic CLI arguments for testing."""
    class Args:
        audio_path = "test.mp3"
        model = "gpt-4o-transcribe"
        detect_model = "gpt-4o-mini-transcribe"
        language = None
        probe_seconds = 25
        no_probe = False
        language_routing = False
        out = None
        temperature = 0.0
        debug = False
        log_dir = "logs"
        enable_file_logging = False
        dry_run = False
        stdin = False
    
    return Args()


@pytest.fixture
def debug_cli_args(basic_cli_args):
    """Create CLI arguments with debug enabled."""
    basic_cli_args.debug = True
    return basic_cli_args


# ============================================================================
# Text Sample Fixtures (for language detection)
# ============================================================================

@pytest.fixture
def portuguese_text():
    """Sample Portuguese text for language detection testing."""
    return "Olá, bom dia. Muito obrigado pela atenção. Isto é um teste de gravação."


@pytest.fixture
def spanish_text():
    """Sample Spanish text for language detection testing."""
    return "Hola, buenos días. Muchas gracias por su atención. Esto es una prueba de grabación."


@pytest.fixture
def english_text():
    """Sample English text for language detection testing."""
    return "Hello, good morning. Thank you very much for your attention. This is a test recording."


@pytest.fixture
def mixed_language_text():
    """Sample text with mixed languages."""
    return "Hello, this is English. Hola, esto es español. Olá, isto é português."


@pytest.fixture
def no_keywords_text():
    """Sample text with no language keywords."""
    return "Lorem ipsum dolor sit amet consectetur adipiscing elit"

