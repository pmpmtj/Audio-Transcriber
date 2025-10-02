"""
Unit tests for dry-run functionality.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.transcribe_audio.cli.transcribe_cli import create_dry_run_result


class TestDryRun:
    """Tests for dry-run functionality."""
    
    def test_dry_run_with_valid_file(self, sample_audio_path, basic_cli_args):
        """Test dry-run with valid audio file."""
        basic_cli_args.audio_path = str(sample_audio_path)
        basic_cli_args.language_routing = True
        
        mock_logger = MagicMock()
        
        result = create_dry_run_result(basic_cli_args, mock_logger)
        
        # Check result structure
        assert result['text'] == "[DRY RUN] This is a mock transcription result. No API calls were made."
        assert result['language'] == "auto-detect"
        assert result['_meta']['dry_run'] is True
        assert result['_meta']['model'] == basic_cli_args.model
        assert result['_meta']['detect_model'] == basic_cli_args.detect_model
        assert result['_meta']['source_file'] == str(sample_audio_path.resolve())
        assert result['_meta']['forced_language'] is False
        assert result['_meta']['language_routing_enabled'] is True
        assert result['_meta']['ffmpeg_available'] is True  # Should be True in test environment
        
        # Check that logger was called
        assert mock_logger.info.called
    
    def test_dry_run_with_nonexistent_file(self, nonexistent_audio_path, basic_cli_args):
        """Test dry-run with nonexistent file raises error."""
        basic_cli_args.audio_path = str(nonexistent_audio_path)
        
        mock_logger = MagicMock()
        
        with pytest.raises(FileNotFoundError):
            create_dry_run_result(basic_cli_args, mock_logger)
    
    def test_dry_run_with_unsupported_extension(self, temp_dir, basic_cli_args):
        """Test dry-run with unsupported file extension raises error."""
        unsupported_file = temp_dir / "test.flac"
        unsupported_file.write_text("fake content")
        basic_cli_args.audio_path = str(unsupported_file)
        
        mock_logger = MagicMock()
        
        with pytest.raises(ValueError) as exc_info:
            create_dry_run_result(basic_cli_args, mock_logger)
        
        assert "Unsupported file type" in str(exc_info.value)
    
    def test_dry_run_with_ffmpeg_unavailable(self, sample_audio_path, basic_cli_args):
        """Test dry-run when FFmpeg is not available."""
        basic_cli_args.audio_path = str(sample_audio_path)
        basic_cli_args.language_routing = True
        
        mock_logger = MagicMock()
        
        with patch('src.transcribe_audio.core.language_detection.have_ffmpeg', return_value=False):
            result = create_dry_run_result(basic_cli_args, mock_logger)
        
        assert result['_meta']['ffmpeg_available'] is False
        assert result['_meta']['ffmpeg_used'] is False
    
    def test_dry_run_without_language_routing(self, sample_audio_path, basic_cli_args):
        """Test dry-run without language routing."""
        basic_cli_args.audio_path = str(sample_audio_path)
        basic_cli_args.language_routing = False
        
        mock_logger = MagicMock()
        
        result = create_dry_run_result(basic_cli_args, mock_logger)
        
        assert result['_meta']['language_routing_enabled'] is False
        assert result['_meta']['routed_language'] is None
        assert result['_meta']['ffmpeg_used'] is False
    
    def test_dry_run_with_forced_language(self, sample_audio_path, basic_cli_args):
        """Test dry-run with forced language."""
        basic_cli_args.audio_path = str(sample_audio_path)
        basic_cli_args.language = "pt"
        basic_cli_args.language_routing = True
        
        mock_logger = MagicMock()
        
        result = create_dry_run_result(basic_cli_args, mock_logger)
        
        assert result['language'] == "pt"
        assert result['_meta']['forced_language'] is True
        assert result['_meta']['routed_language'] is None
        assert result['_meta']['ffmpeg_used'] is False
    
    def test_dry_run_with_no_probe(self, sample_audio_path, basic_cli_args):
        """Test dry-run with probe disabled."""
        basic_cli_args.audio_path = str(sample_audio_path)
        basic_cli_args.language_routing = True
        basic_cli_args.no_probe = True
        
        mock_logger = MagicMock()
        
        result = create_dry_run_result(basic_cli_args, mock_logger)
        
        assert result['_meta']['probe_seconds'] is None
        assert result['_meta']['ffmpeg_used'] is False
    
    def test_dry_run_logs_expected_messages(self, sample_audio_path, basic_cli_args):
        """Test that dry-run logs expected messages."""
        basic_cli_args.audio_path = str(sample_audio_path)
        basic_cli_args.language_routing = True
        
        mock_logger = MagicMock()
        
        create_dry_run_result(basic_cli_args, mock_logger)
        
        # Check that key log messages were called
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        
        # Check for specific log messages that should be present
        assert any("File validation" in call for call in log_calls)
        assert any("FFmpeg available" in call for call in log_calls)
        assert any("API calls that would be made" in call for call in log_calls)
