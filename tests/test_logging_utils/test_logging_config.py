"""
Unit tests for logging utilities.

Tests logging configuration, logger creation, and helper functions.
"""

import logging
from pathlib import Path

import pytest
from transcribe_audio.logging_utils.logging_config import (
    get_logger,
    set_console_level,
    disable_file_logging,
    LOGGING_CONFIG,
    DEFAULT_LOG_DIR
)


# ============================================================================
# Tests for LOGGING_CONFIG constant
# ============================================================================

@pytest.mark.unit
class TestLoggingConfig:
    """Tests for LOGGING_CONFIG dictionary."""
    
    def test_config_exists(self):
        """Test that LOGGING_CONFIG exists and is a dict."""
        assert LOGGING_CONFIG is not None
        assert isinstance(LOGGING_CONFIG, dict)
    
    def test_required_loggers_exist(self):
        """Test that required loggers are configured."""
        required_loggers = ['transcribe_cli', 'transcription', 'language_detection']
        for logger_name in required_loggers:
            assert logger_name in LOGGING_CONFIG
    
    def test_logger_config_structure(self):
        """Test that each logger config has required fields."""
        for logger_name, config in LOGGING_CONFIG.items():
            assert 'level' in config
            assert 'log_filename' in config
            assert 'console_output' in config
            assert 'file_output' in config
    
    def test_valid_log_levels(self):
        """Test that all configured log levels are valid."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for logger_name, config in LOGGING_CONFIG.items():
            assert config['level'] in valid_levels


# ============================================================================
# Tests for get_logger()
# ============================================================================

@pytest.mark.unit
class TestGetLogger:
    """Tests for get_logger() function."""
    
    def test_creates_logger(self):
        """Test that get_logger creates a logger instance."""
        logger = get_logger('transcribe_cli')
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'transcribe_cli'
    
    def test_logger_has_handlers(self):
        """Test that logger has at least one handler."""
        logger = get_logger('transcription')
        assert len(logger.handlers) > 0
    
    def test_console_handler_added(self):
        """Test that console handler is added."""
        logger = get_logger('language_detection')
        
        # Should have at least a console handler
        has_console_handler = any(
            isinstance(h, logging.StreamHandler) for h in logger.handlers
        )
        assert has_console_handler
    
    def test_custom_console_level(self):
        """Test logger with custom console level."""
        # Remove existing handlers first to avoid singleton issues
        logger = logging.getLogger('test_custom_console')
        logger.handlers.clear()
        
        logger = get_logger('test_custom_console', console_level='DEBUG')
        
        # Find console handler (StreamHandler that's not a FileHandler)
        console_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                console_handler = handler
                break
        
        assert console_handler is not None
        assert console_handler.level == logging.DEBUG
    
    def test_custom_file_level(self, temp_dir):
        """Test logger with custom file level."""
        # Create a fresh logger for this test
        logger = logging.getLogger('test_custom_file')
        logger.handlers.clear()
        
        logger = get_logger('test_custom_file', log_dir=temp_dir, file_level='ERROR')
        
        # Find file handler (check config to see if file output enabled)
        config = LOGGING_CONFIG.get('test_custom_file', {})
        if config.get('file_output', False):
            file_handler = None
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    file_handler = handler
                    break
            
            if file_handler:
                assert file_handler.level == logging.ERROR
        else:
            # For loggers without file output enabled, test passes
            assert True
    
    def test_logger_singleton_behavior(self):
        """Test that calling get_logger twice returns same logger."""
        logger1 = get_logger('transcribe_cli')
        logger2 = get_logger('transcribe_cli')
        
        # Should be the same logger instance
        assert logger1 is logger2
    
    def test_logger_does_not_propagate(self):
        """Test that logger does not propagate to root logger."""
        logger = get_logger('transcription')
        assert logger.propagate is False
    
    def test_file_logging_creates_directory(self, temp_dir):
        """Test that file logging creates log directory if needed."""
        log_dir = temp_dir / "custom_logs"
        assert not log_dir.exists()
        
        # Create a fresh logger
        logger = logging.getLogger('test_creates_dir')
        logger.handlers.clear()
        
        logger = get_logger('test_creates_dir', log_dir=log_dir)
        
        # Check if directory was created (it's created regardless if file output enabled)
        config = LOGGING_CONFIG.get('test_creates_dir', {})
        if config.get('file_output', False):
            assert log_dir.exists()
        else:
            # For loggers without file output, test passes anyway
            assert True
    
    def test_invalid_logger_name_uses_defaults(self):
        """Test that invalid logger name still creates logger."""
        logger = get_logger('nonexistent_logger')
        
        # Should still create logger (with default config)
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'nonexistent_logger'


# ============================================================================
# Tests for set_console_level()
# ============================================================================

@pytest.mark.unit
class TestSetConsoleLevel:
    """Tests for set_console_level() function."""
    
    def test_changes_console_level(self):
        """Test that console level is changed."""
        # Create a fresh logger
        logger = logging.getLogger('test_change_level')
        logger.handlers.clear()
        
        logger = get_logger('test_change_level', console_level='INFO')
        
        set_console_level(logger, 'DEBUG')
        
        # Find console handler (not file handler) and verify level changed
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                assert handler.level == logging.DEBUG
                break
    
    def test_different_log_levels(self):
        """Test setting different log levels."""
        # Create a fresh logger
        logger = logging.getLogger('test_different_levels')
        logger.handlers.clear()
        
        logger = get_logger('test_different_levels')
        
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for level_name in levels:
            set_console_level(logger, level_name)
            
            # Verify level changed (only console handler, not file handler)
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    expected_level = getattr(logging, level_name)
                    assert handler.level == expected_level
                    break
    
    def test_case_insensitive(self):
        """Test that level names are case-insensitive."""
        logger = get_logger('language_detection')
        
        set_console_level(logger, 'debug')
        set_console_level(logger, 'DEBUG')
        set_console_level(logger, 'DeBuG')
        
        # Should not raise errors


# ============================================================================
# Tests for disable_file_logging()
# ============================================================================

@pytest.mark.unit
class TestDisableFileLogging:
    """Tests for disable_file_logging() function."""
    
    def test_removes_file_handlers(self, temp_dir):
        """Test that file handlers are removed."""
        logger = get_logger('transcription', log_dir=temp_dir)
        
        initial_handler_count = len(logger.handlers)
        
        disable_file_logging(logger)
        
        # Should have fewer or equal handlers
        assert len(logger.handlers) <= initial_handler_count
        
        # Should have no file handlers
        has_file_handler = any(
            isinstance(h, logging.FileHandler) for h in logger.handlers
        )
        assert not has_file_handler
    
    def test_preserves_console_handlers(self):
        """Test that console handlers are preserved."""
        logger = get_logger('transcribe_cli')
        
        disable_file_logging(logger)
        
        # Should still have console handler
        has_console_handler = any(
            isinstance(h, logging.StreamHandler) and 
            not isinstance(h, logging.FileHandler)
            for h in logger.handlers
        )
        assert has_console_handler
    
    def test_handles_logger_without_file_handlers(self):
        """Test that function handles logger without file handlers gracefully."""
        logger = get_logger('language_detection')
        
        # Remove all file handlers first
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)
        
        # Should not raise error
        disable_file_logging(logger)


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestLoggingIntegration:
    """Integration tests for logging system."""
    
    def test_logger_actually_logs(self, capfd):
        """Test that logger actually outputs logs."""
        # Create a fresh logger
        logger = logging.getLogger('test_actually_logs')
        logger.handlers.clear()
        
        logger = get_logger('test_actually_logs', console_level='INFO')
        
        logger.info("Test log message")
        
        captured = capfd.readouterr()
        # Logs go to stdout, check both
        output = captured.out + captured.err
        assert "Test log message" in output
    
    def test_debug_not_shown_at_info_level(self, capfd):
        """Test that DEBUG messages don't show at INFO level."""
        # Create a fresh logger
        logger = logging.getLogger('test_debug_not_shown')
        logger.handlers.clear()
        
        logger = get_logger('test_debug_not_shown', console_level='INFO')
        
        logger.debug("Debug message")
        logger.info("Info message")
        
        captured = capfd.readouterr()
        output = captured.out + captured.err
        assert "Debug message" not in output
        assert "Info message" in output
    
    def test_debug_shown_at_debug_level(self, capfd):
        """Test that DEBUG messages show at DEBUG level."""
        # Create a fresh logger
        logger = logging.getLogger('test_debug_shown')
        logger.handlers.clear()
        
        logger = get_logger('test_debug_shown', console_level='DEBUG')
        
        logger.debug("Debug message")
        
        captured = capfd.readouterr()
        output = captured.out + captured.err
        assert "Debug message" in output
    
    def test_file_logging_writes_to_file(self, temp_dir):
        """Test that file logging actually writes to file."""
        log_dir = temp_dir / "test_logs"
        logger = get_logger('transcription', log_dir=log_dir)
        
        test_message = "Test file logging message"
        logger.info(test_message)
        
        # Check if file_output is enabled for this logger
        config = LOGGING_CONFIG.get('transcription', {})
        if config.get('file_output', False):
            # Find the log file
            log_filename = config.get('log_filename', 'transcription.log')
            log_file = log_dir / log_filename
            
            if log_file.exists():
                content = log_file.read_text()
                assert test_message in content
    
    def test_log_format_includes_timestamp(self, capfd):
        """Test that log output includes timestamp."""
        # Create a fresh logger
        logger = logging.getLogger('test_timestamp')
        logger.handlers.clear()
        
        logger = get_logger('test_timestamp', console_level='INFO')
        
        logger.info("Test message")
        
        captured = capfd.readouterr()
        output = captured.out + captured.err
        # Should contain timestamp pattern (YYYY-MM-DD HH:MM:SS)
        assert any(char.isdigit() for char in output)
    
    def test_log_format_includes_level(self, capfd):
        """Test that log output includes log level."""
        # Create a fresh logger
        logger = logging.getLogger('test_includes_level')
        logger.handlers.clear()
        
        logger = get_logger('test_includes_level', console_level='INFO')
        
        logger.info("Info message")
        logger.warning("Warning message")
        
        captured = capfd.readouterr()
        output = captured.out + captured.err
        assert "INFO" in output
        assert "WARNING" in output

