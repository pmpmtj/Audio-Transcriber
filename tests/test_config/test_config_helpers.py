"""
Unit tests for configuration helper methods.
"""

import pytest
from unittest.mock import patch
from src.transcribe_audio.config import TranscriptionConfig


class TestConfigHelpers:
    """Tests for configuration helper methods."""
    
    def test_get_probe_model(self):
        """Test get_probe_model() helper method."""
        result = TranscriptionConfig.get_probe_model()
        assert result == TranscriptionConfig.get_model('detect')
        assert result == 'gpt-4o-mini-transcribe'
    
    def test_get_main_model(self):
        """Test get_main_model() helper method."""
        result = TranscriptionConfig.get_main_model()
        assert result == TranscriptionConfig.get_model('main')
        assert result == 'gpt-4o-transcribe'
    
    def test_get_log_dir(self):
        """Test get_log_dir() helper method."""
        result = TranscriptionConfig.get_log_dir()
        assert result == TranscriptionConfig.LOGGING_SETTINGS['log_dir']
        assert result == 'logs'
    
    def test_get_client_with_api_key(self, mock_api_key):
        """Test get_client() with provided API key."""
        client = TranscriptionConfig.get_client(api_key="test-key-123")
        assert client is not None
        # Check that client was created with correct API key
        assert hasattr(client, 'api_key')
    
    def test_get_client_without_api_key_raises_error(self, no_api_key):
        """Test get_client() without API key raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TranscriptionConfig.get_client()
        assert "OPENAI_API_KEY" in str(exc_info.value)
    
    def test_get_client_with_timeout_override(self, mock_api_key):
        """Test get_client() with timeout override."""
        client = TranscriptionConfig.get_client(
            api_key="test-key-123", 
            timeout=600
        )
        assert client is not None
    
    def test_get_client_with_retries_override(self, mock_api_key):
        """Test get_client() with retries override."""
        client = TranscriptionConfig.get_client(
            api_key="test-key-123", 
            max_retries=5
        )
        assert client is not None
    
    def test_load_env_file_nonexistent(self, temp_dir):
        """Test load_env_file() with nonexistent file."""
        result = TranscriptionConfig.load_env_file(temp_dir / "nonexistent.env")
        assert result is False
    
    def test_load_env_file_simple_parsing(self, temp_dir):
        """Test load_env_file() with simple .env parsing (no python-dotenv)."""
        env_file = temp_dir / ".env"
        env_file.write_text("OPENAI_API_KEY=test-key-123\nTEST_VAR=test-value")
        
        # Test the actual function without mocking
        result = TranscriptionConfig.load_env_file(env_file)
        assert result is True
        
        # Check that environment variable was set
        import os
        assert os.getenv("OPENAI_API_KEY") == "test-key-123"
        assert os.getenv("TEST_VAR") == "test-value"
    
    def test_load_env_file_handles_comments_and_empty_lines(self, temp_dir):
        """Test load_env_file() handles comments and empty lines."""
        env_file = temp_dir / ".env"
        env_file.write_text("""
# This is a comment
OPENAI_API_KEY=test-key-123

# Another comment
TEST_VAR=test-value
""")
        
        result = TranscriptionConfig.load_env_file(env_file)
        assert result is True
        
        import os
        assert os.getenv("OPENAI_API_KEY") == "test-key-123"
        assert os.getenv("TEST_VAR") == "test-value"
