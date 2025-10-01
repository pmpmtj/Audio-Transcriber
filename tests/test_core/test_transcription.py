"""
Unit tests for transcription module.

Tests transcribe_full() and transcribe_audio() functions with mocked dependencies.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, PropertyMock

import pytest
from transcribe_audio.core.transcription import (
    transcribe_full,
    transcribe_audio
)


# ============================================================================
# Tests for transcribe_full()
# ============================================================================

@pytest.mark.integration
class TestTranscribeFull:
    """Tests for transcribe_full() function."""
    
    def test_basic_transcription(self, mocker, sample_audio_path, mock_openai_client):
        """Test basic transcription without language parameter."""
        # Setup mock response
        mock_response = Mock()
        mock_response.model_dump.return_value = {
            "text": "This is a test transcription",
            "language": "en"
        }
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        
        # Mock file open
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        
        result = transcribe_full(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            model='gpt-4o-transcribe',
            language=None,
            temperature=0.0
        )
        
        assert result['text'] == "This is a test transcription"
        assert result['language'] == "en"
        assert mock_openai_client.audio.transcriptions.create.called
    
    def test_transcription_with_language(self, mocker, sample_audio_path, mock_openai_client):
        """Test transcription with forced language."""
        mock_response = Mock()
        mock_response.model_dump.return_value = {
            "text": "Olá, isto é um teste",
            "language": "pt"
        }
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        
        result = transcribe_full(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            model='gpt-4o-transcribe',
            language='pt',
            temperature=0.0
        )
        
        # Verify language was passed to API
        call_kwargs = mock_openai_client.audio.transcriptions.create.call_args[1]
        assert 'language' in call_kwargs
        assert call_kwargs['language'] == 'pt'
    
    def test_transcription_with_different_temperature(self, mocker, sample_audio_path, mock_openai_client):
        """Test transcription with non-zero temperature."""
        mock_response = Mock()
        mock_response.model_dump.return_value = {"text": "Test"}
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        
        transcribe_full(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            model='gpt-4o-transcribe',
            language=None,
            temperature=0.5
        )
        
        call_kwargs = mock_openai_client.audio.transcriptions.create.call_args[1]
        assert call_kwargs['temperature'] == 0.5
    
    def test_response_normalization_model_dump(self, mocker, sample_audio_path, mock_openai_client):
        """Test response normalization using model_dump()."""
        mock_response = Mock()
        mock_response.model_dump.return_value = {"text": "Test via model_dump"}
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        
        result = transcribe_full(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            model='gpt-4o-transcribe',
            language=None,
            temperature=0.0
        )
        
        assert result['text'] == "Test via model_dump"
    
    def test_response_normalization_to_dict(self, mocker, sample_audio_path, mock_openai_client):
        """Test response normalization fallback to to_dict()."""
        mock_response = Mock()
        mock_response.model_dump.side_effect = AttributeError("No model_dump")
        mock_response.to_dict.return_value = {"text": "Test via to_dict"}
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        
        result = transcribe_full(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            model='gpt-4o-transcribe',
            language=None,
            temperature=0.0
        )
        
        assert result['text'] == "Test via to_dict"
    
    def test_response_normalization_json_loads(self, mocker, sample_audio_path, mock_openai_client):
        """Test response normalization fallback to json.loads()."""
        mock_response = Mock()
        mock_response.model_dump.side_effect = AttributeError("No model_dump")
        mock_response.to_dict.side_effect = AttributeError("No to_dict")
        # Mock __str__ properly
        mock_response.__str__ = Mock(return_value='{"text": "Test via json.loads"}')
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        
        result = transcribe_full(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            model='gpt-4o-transcribe',
            language=None,
            temperature=0.0
        )
        
        assert result['text'] == "Test via json.loads"


# ============================================================================
# Tests for transcribe_audio()
# ============================================================================

@pytest.mark.integration
class TestTranscribeAudio:
    """Tests for transcribe_audio() main function."""
    
    def test_basic_transcription(self, mocker, sample_audio_path, mock_openai_client):
        """Test basic transcription with default parameters."""
        # Mock transcribe_full
        mock_result = {"text": "Test transcription"}
        mocker.patch('transcribe_audio.core.transcription.transcribe_full', return_value=mock_result)
        
        result = transcribe_audio(
            audio_path=str(sample_audio_path),
            client=mock_openai_client
        )
        
        assert result['text'] == "Test transcription"
        assert '_meta' in result
        assert result['_meta']['source_file'] == str(sample_audio_path)
    
    def test_file_not_found_raises_error(self, mock_openai_client, nonexistent_audio_path):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            transcribe_audio(
                audio_path=str(nonexistent_audio_path),
                client=mock_openai_client
            )
        
        assert "Audio file not found" in str(exc_info.value)
    
    def test_unsupported_file_type_raises_error(self, mocker, temp_dir, mock_openai_client):
        """Test that unsupported file type raises ValueError."""
        # Create unsupported file type
        unsupported_file = temp_dir / "test.flac"
        unsupported_file.write_text("fake content")
        
        with pytest.raises(ValueError) as exc_info:
            transcribe_audio(
                audio_path=str(unsupported_file),
                client=mock_openai_client
            )
        
        assert "Unsupported file type" in str(exc_info.value)
        assert ".flac" in str(exc_info.value)
    
    def test_all_supported_extensions(self, mocker, temp_dir, mock_openai_client):
        """Test that all supported extensions are accepted."""
        mocker.patch('transcribe_audio.core.transcription.transcribe_full', return_value={"text": "Test"})
        
        for ext in ['.mp3', '.m4a', '.wav']:
            audio_file = temp_dir / f"test{ext}"
            audio_file.write_text("fake content")
            
            result = transcribe_audio(
                audio_path=str(audio_file),
                client=mock_openai_client
            )
            
            assert result is not None
            assert '_meta' in result
    
    def test_language_routing_enabled(self, mocker, sample_audio_path, mock_openai_client):
        """Test transcription with language routing enabled."""
        mocker.patch('transcribe_audio.core.transcription.transcribe_full', return_value={"text": "Test"})
        
        # Mock language detection - need to import from the right place
        mock_detect = mocker.patch('transcribe_audio.core.language_detection.detect_language_with_probe')
        mock_detect.return_value = 'pt'
        
        result = transcribe_audio(
            audio_path=str(sample_audio_path),
            language_routing=True,
            client=mock_openai_client
        )
        
        assert result['_meta']['language_routing_enabled'] is True
        assert result['_meta']['routed_language'] == 'pt'
        assert mock_detect.called
    
    def test_language_routing_disabled(self, mocker, sample_audio_path, mock_openai_client):
        """Test transcription with language routing disabled."""
        mocker.patch('transcribe_audio.core.transcription.transcribe_full', return_value={"text": "Test"})
        
        # Mock language detection (should not be called)
        mock_detect = mocker.patch('transcribe_audio.core.language_detection.detect_language_with_probe')
        
        result = transcribe_audio(
            audio_path=str(sample_audio_path),
            language_routing=False,
            client=mock_openai_client
        )
        
        assert result['_meta']['language_routing_enabled'] is False
        assert not mock_detect.called
    
    def test_forced_language_skips_detection(self, mocker, sample_audio_path, mock_openai_client):
        """Test that forced language skips detection even if routing enabled."""
        mocker.patch('transcribe_audio.core.transcription.transcribe_full', return_value={"text": "Test"})
        
        # Mock language detection (should not be called)
        mock_detect = mocker.patch('transcribe_audio.core.language_detection.detect_language_with_probe')
        
        result = transcribe_audio(
            audio_path=str(sample_audio_path),
            language='es',
            language_routing=True,
            client=mock_openai_client
        )
        
        assert result['_meta']['forced_language'] is True
        assert not mock_detect.called
    
    def test_metadata_enrichment(self, mocker, sample_audio_path, mock_openai_client):
        """Test that result metadata is properly enriched."""
        mocker.patch('transcribe_audio.core.transcription.transcribe_full', return_value={"text": "Test"})
        
        result = transcribe_audio(
            audio_path=str(sample_audio_path),
            model='custom-model',
            detect_model='custom-detect',
            language='fr',
            probe_seconds=15,
            use_probe=False,
            language_routing=False,
            temperature=0.3,
            client=mock_openai_client
        )
        
        meta = result['_meta']
        assert meta['model'] == 'custom-model'
        assert meta['detect_model'] == 'custom-detect'
        assert meta['forced_language'] is True
        assert meta['language_routing_enabled'] is False
        assert meta['probe_seconds'] is None  # None when use_probe=False
        assert str(sample_audio_path) in meta['source_file']
    
    def test_client_creation_when_not_provided(self, mocker, sample_audio_path):
        """Test that OpenAI client is created when not provided."""
        # Mock the OpenAI import within the function
        mock_openai_module = mocker.MagicMock()
        mock_client_instance = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client_instance
        
        # Patch the import at the point where it's used
        mocker.patch.dict('sys.modules', {'openai': mock_openai_module})
        
        mocker.patch('transcribe_audio.core.transcription.transcribe_full', return_value={"text": "Test"})
        
        result = transcribe_audio(audio_path=str(sample_audio_path))
        
        # Verify client was created
        assert mock_openai_module.OpenAI.called
    
    def test_uses_config_defaults(self, mocker, sample_audio_path, mock_openai_client):
        """Test that config defaults are used when parameters not specified."""
        mocker.patch('transcribe_audio.core.transcription.transcribe_full', return_value={"text": "Test"})
        
        result = transcribe_audio(
            audio_path=str(sample_audio_path),
            client=mock_openai_client
        )
        
        meta = result['_meta']
        assert meta['model'] == 'gpt-4o-transcribe'  # Default from config
        assert meta['detect_model'] == 'gpt-4o-mini-transcribe'  # Default from config
    
    def test_openai_import_error(self, mocker, sample_audio_path):
        """Test that ImportError is raised when OpenAI SDK not installed."""
        # The import happens inside the function, so we need to make it fail at import time
        # Remove openai from sys.modules if it exists
        import sys
        openai_backup = sys.modules.get('openai')
        
        try:
            # Remove openai module to simulate it not being installed
            if 'openai' in sys.modules:
                del sys.modules['openai']
            
            # Mock the import to fail
            def failing_import(name, *args, **kwargs):
                if name == 'openai':
                    raise ModuleNotFoundError("No module named 'openai'")
                return original_import(name, *args, **kwargs)
            
            import builtins
            original_import = builtins.__import__
            builtins.__import__ = failing_import
            
            try:
                with pytest.raises(ImportError) as exc_info:
                    transcribe_audio(audio_path=str(sample_audio_path))
                
                assert "OpenAI SDK" in str(exc_info.value)
            finally:
                builtins.__import__ = original_import
        finally:
            # Restore openai module if it was there
            if openai_backup is not None:
                sys.modules['openai'] = openai_backup

