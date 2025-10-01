"""
Unit tests for validation helper functions.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from transcribe_audio.core.transcription import validate_audio_file
from transcribe_audio.config import TranscriptionConfig


class TestValidateAudioFile:
    """Tests for validate_audio_file() function."""
    
    def test_valid_mp3_file(self, sample_audio_path):
        """Test validation of valid MP3 file."""
        result = validate_audio_file(str(sample_audio_path))
        assert result == sample_audio_path.resolve()
    
    def test_valid_m4a_file(self, sample_m4a_path):
        """Test validation of valid M4A file."""
        result = validate_audio_file(str(sample_m4a_path))
        assert result == sample_m4a_path.resolve()
    
    def test_valid_wav_file(self, sample_wav_path):
        """Test validation of valid WAV file."""
        result = validate_audio_file(str(sample_wav_path))
        assert result == sample_wav_path.resolve()
    
    def test_nonexistent_file_raises_error(self, nonexistent_audio_path):
        """Test that nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            validate_audio_file(str(nonexistent_audio_path))
    
    def test_unsupported_extension_raises_error(self, temp_dir):
        """Test that unsupported file extension raises ValueError."""
        unsupported_file = temp_dir / "test.flac"
        unsupported_file.write_text("fake content")
        
        with pytest.raises(ValueError) as exc_info:
            validate_audio_file(str(unsupported_file))
        
        assert "Unsupported file type" in str(exc_info.value)
        assert ".flac" in str(exc_info.value)
    
    def test_expands_user_path(self, temp_dir):
        """Test that ~ paths are expanded correctly."""
        # Create a file in temp directory
        test_file = temp_dir / "test.mp3"
        test_file.write_text("fake content")
        
        # Mock Path.expanduser to return our temp file
        with patch.object(Path, 'expanduser') as mock_expand:
            mock_expand.return_value = test_file
            result = validate_audio_file("~/test.mp3")
            assert result == test_file.resolve()
    
    def test_resolves_relative_path(self, temp_dir):
        """Test that relative paths are resolved."""
        test_file = temp_dir / "test.mp3"
        test_file.write_text("fake content")
        
        with patch.object(Path, 'resolve') as mock_resolve:
            mock_resolve.return_value = test_file
            result = validate_audio_file("test.mp3")
            assert result == test_file
