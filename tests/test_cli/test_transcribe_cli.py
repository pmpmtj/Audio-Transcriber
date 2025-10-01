"""
Unit tests for CLI module.

Tests all CLI functions including argument parsing, logging setup, and main workflow.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from argparse import Namespace

import pytest
from transcribe_audio.cli.transcribe_cli import (
    die,
    parse_args,
    ensure_api_key,
    setup_logging_from_args,
    perform_transcription,
    log_language_detection_info,
    output_transcription_result
)


# ============================================================================
# Tests for die()
# ============================================================================

@pytest.mark.unit
class TestDie:
    """Tests for die() function."""
    
    def test_die_exits_with_code(self, mocker):
        """Test that die() exits with specified code."""
        mock_exit = mocker.patch('sys.exit')
        
        die("Test error", 42)
        
        mock_exit.assert_called_once_with(42)
    
    def test_die_prints_error_message(self, capsys, mocker):
        """Test that die() prints error message to stderr."""
        mocker.patch('sys.exit')
        
        die("Test error message", 1)
        
        captured = capsys.readouterr()
        assert "ERROR: Test error message" in captured.err
    
    def test_die_with_different_exit_codes(self, mocker):
        """Test die() with various exit codes."""
        mock_exit = mocker.patch('sys.exit')
        
        for code in [0, 1, 2, 3, 4, 127]:
            die(f"Error {code}", code)
            assert mock_exit.call_args[0][0] == code


# ============================================================================
# Tests for parse_args()
# ============================================================================

@pytest.mark.unit
class TestParseArgs:
    """Tests for parse_args() function."""
    
    def test_basic_arguments(self, mocker):
        """Test parsing basic required arguments."""
        mocker.patch('sys.argv', ['transcribe_cli.py', 'test.mp3'])
        
        args = parse_args()
        
        assert args.audio_path == 'test.mp3'
        assert args.model == 'gpt-4o-transcribe'
        assert args.temperature == 0.0
    
    def test_all_optional_arguments(self, mocker):
        """Test parsing all optional arguments."""
        mocker.patch('sys.argv', [
            'transcribe_cli.py',
            'test.mp3',
            '--model', 'custom-model',
            '--detect-model', 'custom-detect',
            '--language', 'pt',
            '--probe-seconds', '30',
            '--no-probe',
            '--language-routing',
            '--out', 'output.json',
            '--temperature', '0.5',
            '--debug',
            '--log-dir', '/tmp/logs',
            '--enable-file-logging'
        ])
        
        args = parse_args()
        
        assert args.audio_path == 'test.mp3'
        assert args.model == 'custom-model'
        assert args.detect_model == 'custom-detect'
        assert args.language == 'pt'
        assert args.probe_seconds == 30
        assert args.no_probe is True
        assert args.language_routing is True
        assert args.out == 'output.json'
        assert args.temperature == 0.5
        assert args.debug is True
        assert args.log_dir == '/tmp/logs'
        assert args.enable_file_logging is True
    
    def test_default_values(self, mocker):
        """Test that default values are set correctly."""
        mocker.patch('sys.argv', ['transcribe_cli.py', 'test.mp3'])
        
        args = parse_args()
        
        assert args.model == 'gpt-4o-transcribe'
        assert args.detect_model == 'gpt-4o-mini-transcribe'
        assert args.language is None
        assert args.probe_seconds == 25
        assert args.no_probe is False
        assert args.language_routing is False
        assert args.out is None
        assert args.temperature == 0.0
        assert args.debug is False
        assert args.log_dir == 'logs'
        assert args.enable_file_logging is False


# ============================================================================
# Tests for ensure_api_key()
# ============================================================================

@pytest.mark.unit
class TestEnsureApiKey:
    """Tests for ensure_api_key() function."""
    
    def test_api_key_present(self, mock_api_key):
        """Test that function passes when API key is present."""
        # Should not raise any exception
        ensure_api_key()
    
    def test_api_key_missing_raises_error(self, no_api_key, mocker):
        """Test that missing API key calls die()."""
        mock_die = mocker.patch('transcribe_audio.cli.transcribe_cli.die')
        
        ensure_api_key()
        
        assert mock_die.called
        assert "OPENAI_API_KEY" in mock_die.call_args[0][0]


# ============================================================================
# Tests for setup_logging_from_args()
# ============================================================================

@pytest.mark.unit
class TestSetupLoggingFromArgs:
    """Tests for setup_logging_from_args() function."""
    
    def test_setup_with_debug_flag(self, mocker, basic_cli_args):
        """Test logging setup with debug flag enabled."""
        basic_cli_args.debug = True
        mock_get_logger = mocker.patch('transcribe_audio.cli.transcribe_cli.get_logger')
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger = setup_logging_from_args(basic_cli_args)
        
        # Should create logger with DEBUG level
        call_kwargs = mock_get_logger.call_args[1]
        assert call_kwargs['console_level'] == 'DEBUG'
    
    def test_setup_without_debug_flag(self, mocker, basic_cli_args):
        """Test logging setup without debug flag."""
        basic_cli_args.debug = False
        mock_get_logger = mocker.patch('transcribe_audio.cli.transcribe_cli.get_logger')
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger = setup_logging_from_args(basic_cli_args)
        
        # Should create logger with INFO level
        call_kwargs = mock_get_logger.call_args[1]
        assert call_kwargs['console_level'] == 'INFO'
    
    def test_file_logging_enabled(self, mocker, basic_cli_args):
        """Test logging setup with file logging enabled."""
        basic_cli_args.enable_file_logging = True
        basic_cli_args.log_dir = '/custom/logs'
        mock_get_logger = mocker.patch('transcribe_audio.cli.transcribe_cli.get_logger')
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_disable = mocker.patch('transcribe_audio.cli.transcribe_cli.disable_file_logging')
        
        logger = setup_logging_from_args(basic_cli_args)
        
        # Should not disable file logging
        assert not mock_disable.called
        
        # Should pass log_dir
        call_kwargs = mock_get_logger.call_args[1]
        assert call_kwargs['log_dir'] is not None
    
    def test_file_logging_disabled(self, mocker, basic_cli_args):
        """Test logging setup with file logging disabled."""
        basic_cli_args.enable_file_logging = False
        mock_get_logger = mocker.patch('transcribe_audio.cli.transcribe_cli.get_logger')
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_disable = mocker.patch('transcribe_audio.cli.transcribe_cli.disable_file_logging')
        
        logger = setup_logging_from_args(basic_cli_args)
        
        # Should disable file logging
        mock_disable.assert_called_once_with(mock_logger)


# ============================================================================
# Tests for perform_transcription()
# ============================================================================

@pytest.mark.integration
class TestPerformTranscription:
    """Tests for perform_transcription() function."""
    
    def test_successful_transcription(self, mocker, basic_cli_args):
        """Test successful transcription."""
        mock_logger = MagicMock()
        mock_result = {"text": "Test transcription", "_meta": {}}
        mock_transcribe = mocker.patch('transcribe_audio.cli.transcribe_cli.transcribe_audio')
        mock_transcribe.return_value = mock_result
        
        result = perform_transcription(basic_cli_args, mock_logger)
        
        assert result == mock_result
        assert mock_transcribe.called
        assert mock_logger.info.called
        assert mock_logger.debug.called
    
    def test_passes_all_arguments(self, mocker, basic_cli_args):
        """Test that all arguments are passed to transcribe_audio."""
        mock_logger = MagicMock()
        mock_transcribe = mocker.patch('transcribe_audio.cli.transcribe_cli.transcribe_audio')
        mock_transcribe.return_value = {"text": "Test"}
        
        basic_cli_args.language = 'pt'
        basic_cli_args.language_routing = True
        basic_cli_args.probe_seconds = 30
        
        perform_transcription(basic_cli_args, mock_logger)
        
        call_kwargs = mock_transcribe.call_args[1]
        assert call_kwargs['audio_path'] == basic_cli_args.audio_path
        assert call_kwargs['model'] == basic_cli_args.model
        assert call_kwargs['language'] == 'pt'
        assert call_kwargs['language_routing'] is True
        assert call_kwargs['probe_seconds'] == 30


# ============================================================================
# Tests for log_language_detection_info()
# ============================================================================

@pytest.mark.unit
class TestLogLanguageDetectionInfo:
    """Tests for log_language_detection_info() function."""
    
    def test_logs_detected_language(self, basic_cli_args):
        """Test logging when language is detected."""
        mock_logger = MagicMock()
        basic_cli_args.language_routing = True
        basic_cli_args.language = None
        result = {"_meta": {"routed_language": "pt", "ffmpeg_used": True}}
        
        log_language_detection_info(basic_cli_args, result, mock_logger)
        
        assert mock_logger.info.called
        # Check that "pt" appears in any of the log calls
        all_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("pt" in call for call in all_calls)
    
    def test_logs_detection_failure(self, basic_cli_args):
        """Test logging when detection fails."""
        mock_logger = MagicMock()
        basic_cli_args.language_routing = True
        basic_cli_args.language = None
        result = {"_meta": {"routed_language": None}}
        
        log_language_detection_info(basic_cli_args, result, mock_logger)
        
        assert mock_logger.info.called
        call_args = str(mock_logger.info.call_args)
        assert "failed" in call_args.lower() or "auto-detect" in call_args.lower()
    
    def test_logs_routing_disabled(self, basic_cli_args):
        """Test logging when routing is disabled."""
        mock_logger = MagicMock()
        basic_cli_args.language_routing = False
        basic_cli_args.language = None
        result = {"_meta": {}}
        
        log_language_detection_info(basic_cli_args, result, mock_logger)
        
        assert mock_logger.info.called
    
    def test_no_logging_with_forced_language(self, basic_cli_args):
        """Test no detection logging when language is forced."""
        mock_logger = MagicMock()
        basic_cli_args.language_routing = True
        basic_cli_args.language = 'es'
        result = {"_meta": {}}
        
        log_language_detection_info(basic_cli_args, result, mock_logger)
        
        # Should not log detection info
        assert not mock_logger.info.called


# ============================================================================
# Tests for output_transcription_result()
# ============================================================================

@pytest.mark.integration
class TestOutputTranscriptionResult:
    """Tests for output_transcription_result() function."""
    
    def test_output_to_stdout(self, capsys, mocker):
        """Test output to stdout when no file specified."""
        mock_logger = MagicMock()
        result = {"text": "Test transcription", "language": "en"}
        
        output_transcription_result(result, None, mock_logger)
        
        captured = capsys.readouterr()
        assert "Test transcription" in captured.out
        assert mock_logger.debug.called
    
    def test_output_to_file(self, temp_dir, mocker):
        """Test output to file."""
        mock_logger = MagicMock()
        result = {"text": "Test transcription", "language": "en"}
        output_path = temp_dir / "output.json"
        
        output_transcription_result(result, str(output_path), mock_logger)
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify content
        content = json.loads(output_path.read_text(encoding='utf-8'))
        assert content['text'] == "Test transcription"
        assert content['language'] == "en"
        
        # Verify logging
        assert mock_logger.info.called
    
    def test_output_json_formatting(self, capsys, mocker):
        """Test that output is properly formatted JSON."""
        mock_logger = MagicMock()
        result = {"text": "Test", "nested": {"key": "value"}}
        
        output_transcription_result(result, None, mock_logger)
        
        captured = capsys.readouterr()
        # Should be valid JSON
        parsed = json.loads(captured.out)
        assert parsed['text'] == "Test"
        assert parsed['nested']['key'] == "value"
    
    def test_output_preserves_unicode(self, capsys, mocker):
        """Test that Unicode characters are preserved."""
        mock_logger = MagicMock()
        result = {"text": "Olá, obrigado! 你好"}
        
        output_transcription_result(result, None, mock_logger)
        
        captured = capsys.readouterr()
        assert "Olá" in captured.out
        assert "obrigado" in captured.out
        assert "你好" in captured.out

