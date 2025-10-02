"""
Unit tests for TranscriptionConfig class.

Tests all configuration helper methods and settings validation.
"""

import pytest
from src.transcribe_audio.config import TranscriptionConfig


# ============================================================================
# Tests for get_model()
# ============================================================================

@pytest.mark.unit
class TestGetModel:
    """Tests for TranscriptionConfig.get_model()"""
    
    def test_get_main_model(self):
        """Test retrieving main transcription model."""
        model = TranscriptionConfig.get_model('main')
        assert model == 'gpt-4o-transcribe'
        assert isinstance(model, str)
    
    def test_get_detect_model(self):
        """Test retrieving detection model."""
        model = TranscriptionConfig.get_model('detect')
        assert model == 'gpt-4o-mini-transcribe'
        assert isinstance(model, str)
    
    def test_get_model_default(self):
        """Test get_model returns main model when type not specified."""
        model = TranscriptionConfig.get_model()
        assert model == 'gpt-4o-transcribe'
    
    def test_get_model_invalid_type(self):
        """Test get_model returns main model for invalid type."""
        model = TranscriptionConfig.get_model('nonexistent')
        assert model == 'gpt-4o-transcribe'


# ============================================================================
# Tests for get_default()
# ============================================================================

@pytest.mark.unit
class TestGetDefault:
    """Tests for TranscriptionConfig.get_default()"""
    
    def test_get_temperature_default(self):
        """Test retrieving temperature default."""
        temp = TranscriptionConfig.get_default('temperature')
        assert temp == 0.0
        assert isinstance(temp, float)
    
    def test_get_probe_seconds_default(self):
        """Test retrieving probe_seconds default."""
        seconds = TranscriptionConfig.get_default('probe_seconds')
        assert seconds == 25
        assert isinstance(seconds, int)
    
    def test_get_language_routing_default(self):
        """Test retrieving language_routing default."""
        routing = TranscriptionConfig.get_default('language_routing')
        assert routing is False
        assert isinstance(routing, bool)
    
    def test_get_default_with_fallback(self):
        """Test get_default returns fallback for missing key."""
        value = TranscriptionConfig.get_default('nonexistent', 'fallback')
        assert value == 'fallback'
    
    def test_get_default_without_fallback(self):
        """Test get_default returns None for missing key without fallback."""
        value = TranscriptionConfig.get_default('nonexistent')
        assert value is None


# ============================================================================
# Tests for get_language_keywords()
# ============================================================================

@pytest.mark.unit
class TestGetLanguageKeywords:
    """Tests for TranscriptionConfig.get_language_keywords()"""
    
    def test_get_portuguese_keywords(self):
        """Test retrieving Portuguese keywords."""
        keywords = TranscriptionConfig.get_language_keywords('pt')
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert 'obrigado' in keywords
        assert 'olá' in keywords
    
    def test_get_spanish_keywords(self):
        """Test retrieving Spanish keywords."""
        keywords = TranscriptionConfig.get_language_keywords('es')
        assert isinstance(keywords, list)
        assert 'gracias' in keywords
        assert 'hola' in keywords
    
    def test_get_english_keywords(self):
        """Test retrieving English keywords."""
        keywords = TranscriptionConfig.get_language_keywords('en')
        assert isinstance(keywords, list)
        assert 'thank you' in keywords
        assert 'hello' in keywords
    
    def test_get_keywords_invalid_language(self):
        """Test get_language_keywords returns empty list for invalid language."""
        keywords = TranscriptionConfig.get_language_keywords('xyz')
        assert keywords == []
        assert isinstance(keywords, list)
    
    def test_all_supported_languages_have_keywords(self):
        """Test that all supported languages have keyword lists."""
        for lang in TranscriptionConfig.get_supported_languages():
            keywords = TranscriptionConfig.get_language_keywords(lang)
            assert isinstance(keywords, list)
            assert len(keywords) > 0, f"Language {lang} has no keywords"


# ============================================================================
# Tests for get_supported_languages()
# ============================================================================

@pytest.mark.unit
class TestGetSupportedLanguages:
    """Tests for TranscriptionConfig.get_supported_languages()"""
    
    def test_returns_list(self):
        """Test get_supported_languages returns a list."""
        languages = TranscriptionConfig.get_supported_languages()
        assert isinstance(languages, list)
    
    def test_contains_expected_languages(self):
        """Test that common languages are in the list."""
        languages = TranscriptionConfig.get_supported_languages()
        expected = ['pt', 'es', 'en', 'fr', 'de', 'it', 'nl', 'ru', 'zh', 'ja']
        for lang in expected:
            assert lang in languages, f"Expected language {lang} not found"
    
    def test_no_duplicates(self):
        """Test that language list has no duplicates."""
        languages = TranscriptionConfig.get_supported_languages()
        assert len(languages) == len(set(languages))
    
    def test_all_are_strings(self):
        """Test that all language codes are strings."""
        languages = TranscriptionConfig.get_supported_languages()
        assert all(isinstance(lang, str) for lang in languages)


# ============================================================================
# Tests for is_extension_allowed()
# ============================================================================

@pytest.mark.unit
class TestIsExtensionAllowed:
    """Tests for TranscriptionConfig.is_extension_allowed()"""
    
    def test_mp3_with_dot(self):
        """Test that .mp3 is allowed."""
        assert TranscriptionConfig.is_extension_allowed('.mp3') is True
    
    def test_mp3_without_dot(self):
        """Test that mp3 (without dot) is allowed."""
        assert TranscriptionConfig.is_extension_allowed('mp3') is True
    
    def test_m4a_with_dot(self):
        """Test that .m4a is allowed."""
        assert TranscriptionConfig.is_extension_allowed('.m4a') is True
    
    def test_m4a_without_dot(self):
        """Test that m4a (without dot) is allowed."""
        assert TranscriptionConfig.is_extension_allowed('m4a') is True
    
    def test_wav_with_dot(self):
        """Test that .wav is allowed."""
        assert TranscriptionConfig.is_extension_allowed('.wav') is True
    
    def test_wav_without_dot(self):
        """Test that wav (without dot) is allowed."""
        assert TranscriptionConfig.is_extension_allowed('wav') is True
    
    def test_uppercase_extension(self):
        """Test that uppercase extensions are allowed."""
        assert TranscriptionConfig.is_extension_allowed('.MP3') is True
        assert TranscriptionConfig.is_extension_allowed('M4A') is True
    
    def test_invalid_extension(self):
        """Test that invalid extensions are rejected."""
        assert TranscriptionConfig.is_extension_allowed('.flac') is False
        assert TranscriptionConfig.is_extension_allowed('.ogg') is False
        assert TranscriptionConfig.is_extension_allowed('txt') is False
    
    def test_empty_extension(self):
        """Test that empty extension is rejected."""
        assert TranscriptionConfig.is_extension_allowed('') is False
        assert TranscriptionConfig.is_extension_allowed('.') is False


# ============================================================================
# Tests for Configuration Constants
# ============================================================================

@pytest.mark.unit
class TestConfigurationConstants:
    """Tests for configuration constants and structure."""
    
    def test_models_dict_exists(self):
        """Test MODELS dictionary exists and has correct structure."""
        assert hasattr(TranscriptionConfig, 'MODELS')
        assert isinstance(TranscriptionConfig.MODELS, dict)
        assert 'main' in TranscriptionConfig.MODELS
        assert 'detect' in TranscriptionConfig.MODELS
    
    def test_allowed_extensions_exists(self):
        """Test ALLOWED_EXTENSIONS set exists."""
        assert hasattr(TranscriptionConfig, 'ALLOWED_EXTENSIONS')
        assert isinstance(TranscriptionConfig.ALLOWED_EXTENSIONS, set)
        assert len(TranscriptionConfig.ALLOWED_EXTENSIONS) >= 3
    
    def test_defaults_dict_exists(self):
        """Test DEFAULTS dictionary exists."""
        assert hasattr(TranscriptionConfig, 'DEFAULTS')
        assert isinstance(TranscriptionConfig.DEFAULTS, dict)
        assert 'temperature' in TranscriptionConfig.DEFAULTS
        assert 'probe_seconds' in TranscriptionConfig.DEFAULTS
    
    def test_language_keywords_dict_exists(self):
        """Test LANGUAGE_KEYWORDS dictionary exists."""
        assert hasattr(TranscriptionConfig, 'LANGUAGE_KEYWORDS')
        assert isinstance(TranscriptionConfig.LANGUAGE_KEYWORDS, dict)
        assert len(TranscriptionConfig.LANGUAGE_KEYWORDS) >= 10
    
    def test_exit_codes_dict_exists(self):
        """Test EXIT_CODES dictionary exists."""
        assert hasattr(TranscriptionConfig, 'EXIT_CODES')
        assert isinstance(TranscriptionConfig.EXIT_CODES, dict)
        assert 'success' in TranscriptionConfig.EXIT_CODES
        assert 'usage_error' in TranscriptionConfig.EXIT_CODES
        assert TranscriptionConfig.EXIT_CODES['success'] == 0

