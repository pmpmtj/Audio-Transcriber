"""
Unit tests for language detection functions with mocked dependencies.

Tests functions that interact with ffmpeg, file system, and OpenAI API.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call

import pytest
from src.transcribe_audio.core.language_detection import (
    slice_with_ffmpeg,
    detect_language_with_probe
)


# ============================================================================
# Tests for slice_with_ffmpeg()
# ============================================================================

@pytest.mark.integration
class TestSliceWithFFmpeg:
    """Tests for slice_with_ffmpeg() function."""
    
    def test_successful_slice_creation(self, mocker, sample_audio_path):
        """Test successful creation of audio slice with ffmpeg."""
        # Mock subprocess.run to simulate successful ffmpeg execution
        mock_run = mocker.patch('subprocess.run')
        
        # Mock tempfile.mkdtemp to return predictable path
        mock_temp_dir = '/tmp/stt_probe_test123'
        mocker.patch('tempfile.mkdtemp', return_value=mock_temp_dir)
        
        result = slice_with_ffmpeg(sample_audio_path, 25)
        
        # Verify subprocess.run was called
        assert mock_run.called
        
        # Verify the command includes expected parameters
        call_args = mock_run.call_args[0][0]
        assert 'ffmpeg' in call_args
        assert '-t' in call_args
        assert '25' in call_args
        
        # Verify return path
        expected_path = Path(mock_temp_dir) / "probe.wav"
        assert result == expected_path
    
    def test_ffmpeg_failure_returns_invalid_path(self, mocker, sample_audio_path, capsys):
        """Test that ffmpeg failure returns invalid path."""
        # Mock subprocess.run to raise CalledProcessError - need to catch it properly
        from subprocess import CalledProcessError
        mocker.patch('subprocess.run', side_effect=CalledProcessError(1, 'ffmpeg'))
        mocker.patch('tempfile.mkdtemp', return_value='/tmp/test')
        
        result = slice_with_ffmpeg(sample_audio_path, 25)
        
        # Should return special failure path
        assert result == Path("/__ffmpeg_failed__.wav")
        assert not result.exists()
        
        # Should print warning
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "ffmpeg failed" in captured.err.lower()
    
    def test_uses_config_settings(self, mocker, sample_audio_path):
        """Test that function uses settings from TranscriptionConfig."""
        mock_run = mocker.patch('subprocess.run')
        mocker.patch('tempfile.mkdtemp', return_value='/tmp/test')
        
        slice_with_ffmpeg(sample_audio_path, 30)
        
        # Verify config settings are used
        call_args = mock_run.call_args[0][0]
        assert '-ac' in call_args  # audio channels
        assert '-ar' in call_args  # sample rate
        assert '-hide_banner' in call_args
        assert '-loglevel' in call_args
    
    def test_different_durations(self, mocker, sample_audio_path):
        """Test slicing with different durations."""
        mock_run = mocker.patch('subprocess.run')
        mocker.patch('tempfile.mkdtemp', return_value='/tmp/test')
        
        for duration in [5, 10, 15, 30, 60]:
            slice_with_ffmpeg(sample_audio_path, duration)
            call_args = mock_run.call_args[0][0]
            assert str(duration) in call_args


# ============================================================================
# Tests for detect_language_with_probe()
# ============================================================================

@pytest.mark.integration
class TestDetectLanguageWithProbe:
    """Tests for detect_language_with_probe() function."""
    
    def test_detection_with_ffmpeg_probe(self, mocker, sample_audio_path, mock_openai_client):
        """Test language detection using ffmpeg probe."""
        # Create a mock probe path that exists
        probe_path = Path('/tmp/probe.wav')
        
        # Mock ffmpeg availability and slice creation
        mocker.patch('src.transcribe_audio.core.language_detection.have_ffmpeg', return_value=True)
        mocker.patch('src.transcribe_audio.core.language_detection.slice_with_ffmpeg', return_value=probe_path)
        
        # Mock Path.exists to return True for the probe path
        original_exists = Path.exists
        def mock_exists(self):
            if str(self) == '/tmp/probe.wav':
                return True
            return original_exists(self)
        mocker.patch.object(Path, 'exists', mock_exists)
        
        # Mock file open and API response
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        mock_response = "Olá, muito obrigado pela atenção"
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        
        # Mock Path operations for cleanup
        mocker.patch.object(Path, 'unlink')
        mocker.patch.object(Path, 'rmdir')
        
        result = detect_language_with_probe(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            detect_model='gpt-4o-mini-transcribe',
            probe_seconds=25,
            use_probe=True
        )
        
        language, ffmpeg_used = result
        assert language == 'pt'
        assert ffmpeg_used == False  # FFmpeg probe failed in this test
        assert mock_openai_client.audio.transcriptions.create.called
    
    def test_detection_without_ffmpeg(self, mocker, sample_audio_path, mock_openai_client):
        """Test language detection when ffmpeg is not available."""
        # Mock ffmpeg as not available
        mocker.patch('src.transcribe_audio.core.language_detection.have_ffmpeg', return_value=False)
        
        # Mock file open and API response
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        mock_response = "Hello, thank you very much"
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        
        result = detect_language_with_probe(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            detect_model='gpt-4o-mini-transcribe',
            probe_seconds=25,
            use_probe=True
        )
        
        # Should use full file and detect English
        language, ffmpeg_used = result
        assert language == 'en'
        assert ffmpeg_used == False  # FFmpeg not available
    
    def test_detection_with_probe_disabled(self, mocker, sample_audio_path, mock_openai_client):
        """Test language detection when probe is explicitly disabled."""
        # Mock file open and API response
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        mock_response = "Gracias por su atención"
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        
        result = detect_language_with_probe(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            detect_model='gpt-4o-mini-transcribe',
            probe_seconds=25,
            use_probe=False
        )
        
        # Should use full file and detect Spanish
        language, ffmpeg_used = result
        assert language == 'es'
        assert ffmpeg_used == False  # Probe disabled
    
    def test_detection_no_keywords_returns_none(self, mocker, sample_audio_path, mock_openai_client):
        """Test that detection returns None when no keywords match."""
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        mock_response = "Lorem ipsum dolor sit amet"
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        
        result = detect_language_with_probe(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            detect_model='gpt-4o-mini-transcribe',
            probe_seconds=25,
            use_probe=False
        )
        
        language, ffmpeg_used = result
        assert language is None
        assert ffmpeg_used == False  # Probe disabled
    
    def test_api_error_returns_none(self, mocker, sample_audio_path, mock_openai_client, capsys):
        """Test that API errors return None gracefully."""
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        mock_openai_client.audio.transcriptions.create.side_effect = Exception("API Error")
        
        result = detect_language_with_probe(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            detect_model='gpt-4o-mini-transcribe',
            probe_seconds=25,
            use_probe=False
        )
        
        language, ffmpeg_used = result
        assert language is None
        assert ffmpeg_used == False  # Probe disabled
        
        # Should print warning
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
    
    def test_ffmpeg_failure_falls_back_to_full_file(self, mocker, sample_audio_path, mock_openai_client):
        """Test that ffmpeg failure results in fallback to full file."""
        # Mock ffmpeg available but slice creation fails
        mocker.patch('src.transcribe_audio.core.language_detection.have_ffmpeg', return_value=True)
        failed_path = Path("/__ffmpeg_failed__.wav")
        mocker.patch('src.transcribe_audio.core.language_detection.slice_with_ffmpeg', return_value=failed_path)
        
        # Mock Path.exists to return False for failed path
        original_exists = Path.exists
        def mock_exists(self):
            if str(self) == '/__ffmpeg_failed__.wav':
                return False
            return original_exists(self)
        mocker.patch.object(Path, 'exists', mock_exists)
        
        # Mock file open and API response
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        mock_response = "Bonjour, merci beaucoup"
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        
        result = detect_language_with_probe(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            detect_model='gpt-4o-mini-transcribe',
            probe_seconds=25,
            use_probe=True
        )
        
        # Should still work using full file
        language, ffmpeg_used = result
        assert language == 'fr'
        assert ffmpeg_used == False  # FFmpeg probe failed
    
    def test_cleanup_probe_file_on_success(self, mocker, sample_audio_path, mock_openai_client):
        """Test that temporary probe file is cleaned up after use."""
        # Create a temporary actual file to ensure cleanup path exists
        import tempfile
        import os
        
        # Create temporary directory and file
        temp_dir = tempfile.mkdtemp(prefix='stt_probe_test_')
        probe_path = Path(temp_dir) / 'probe.wav'
        probe_path.touch()  # Create the file
        
        # Mock ffmpeg and probe creation to return our actual temp file
        mocker.patch('src.transcribe_audio.core.language_detection.have_ffmpeg', return_value=True)
        mocker.patch('src.transcribe_audio.core.language_detection.slice_with_ffmpeg', return_value=probe_path)
        
        # Mock file operations
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        mock_response = "Olá muito obrigado"  # Portuguese text
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        
        detect_language_with_probe(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            detect_model='gpt-4o-mini-transcribe',
            probe_seconds=25,
            use_probe=True
        )
        
        # Verify cleanup happened - file and directory should be removed
        assert not probe_path.exists()
        assert not Path(temp_dir).exists()
    
    def test_cleanup_on_error(self, mocker, sample_audio_path, mock_openai_client):
        """Test that cleanup happens even when API call fails."""
        # Create a temporary actual file to ensure cleanup path exists
        import tempfile
        
        # Create temporary directory and file
        temp_dir = tempfile.mkdtemp(prefix='stt_probe_test_')
        probe_path = Path(temp_dir) / 'probe.wav'
        probe_path.touch()  # Create the file
        
        # Mock ffmpeg and probe creation to return our actual temp file
        mocker.patch('src.transcribe_audio.core.language_detection.have_ffmpeg', return_value=True)
        mocker.patch('src.transcribe_audio.core.language_detection.slice_with_ffmpeg', return_value=probe_path)
        
        # Mock file operations
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake audio'))
        mock_openai_client.audio.transcriptions.create.side_effect = Exception("API Error")
        
        result = detect_language_with_probe(
            client=mock_openai_client,
            audio_path=sample_audio_path,
            detect_model='gpt-4o-mini-transcribe',
            probe_seconds=25,
            use_probe=True
        )
        
        # Should return None due to error
        language, ffmpeg_used = result
        assert language is None
        assert ffmpeg_used == True  # FFmpeg probe was used before error
        
        # But cleanup should still happen - file and directory should be removed
        assert not probe_path.exists()
        assert not Path(temp_dir).exists()

