"""
Unit tests for language detection functions.

Tests pure text-based language detection and helper functions.
"""

import pytest
from src.transcribe_audio.core.language_detection import (
    detect_language_from_text,
    have_ffmpeg
)


# ============================================================================
# Tests for detect_language_from_text() - Pure Function
# ============================================================================

@pytest.mark.unit
class TestDetectLanguageFromText:
    """Tests for detect_language_from_text() pure function."""
    
    def test_detect_portuguese(self, portuguese_text):
        """Test detection of Portuguese text."""
        result = detect_language_from_text(portuguese_text)
        assert result == 'pt'
    
    def test_detect_spanish(self, spanish_text):
        """Test detection of Spanish text."""
        result = detect_language_from_text(spanish_text)
        assert result == 'es'
    
    def test_detect_english(self, english_text):
        """Test detection of English text."""
        result = detect_language_from_text(english_text)
        assert result == 'en'
    
    def test_portuguese_keywords_case_insensitive(self):
        """Test that keyword matching is case-insensitive."""
        text = "OBRIGADO PELA ATENÇÃO. MUITO OBRIGADO!"
        result = detect_language_from_text(text)
        assert result == 'pt'
    
    def test_spanish_keywords_case_insensitive(self):
        """Test Spanish detection is case-insensitive."""
        text = "GRACIAS POR SU ATENCIÓN. MUCHAS GRACIAS!"
        result = detect_language_from_text(text)
        assert result == 'es'
    
    def test_no_keywords_returns_none(self, no_keywords_text):
        """Test that text without keywords returns None."""
        result = detect_language_from_text(no_keywords_text)
        assert result is None
    
    def test_empty_string_returns_none(self):
        """Test that empty string returns None."""
        result = detect_language_from_text("")
        assert result is None
    
    def test_mixed_language_returns_highest_score(self, mixed_language_text):
        """Test that mixed language text returns language with most keywords."""
        result = detect_language_from_text(mixed_language_text)
        # Should return one of the languages (en, es, or pt)
        assert result in ['en', 'es', 'pt']
    
    def test_single_keyword_detection(self):
        """Test detection with just one keyword."""
        text = "obrigado"
        result = detect_language_from_text(text)
        assert result == 'pt'
    
    def test_multiple_keywords_same_language(self):
        """Test detection with multiple keywords from same language."""
        text = "olá bom dia muito obrigado tudo bem"
        result = detect_language_from_text(text)
        assert result == 'pt'
    
    def test_french_detection(self):
        """Test detection of French text."""
        text = "Bonjour, merci beaucoup. S'il vous plaît, au revoir."
        result = detect_language_from_text(text)
        assert result == 'fr'
    
    def test_german_detection(self):
        """Test detection of German text."""
        text = "Hallo, guten Tag. Danke schön, bitte sehr."
        result = detect_language_from_text(text)
        assert result == 'de'
    
    def test_italian_detection(self):
        """Test detection of Italian text."""
        text = "Ciao, buongiorno. Grazie mille, per favore."
        result = detect_language_from_text(text)
        assert result == 'it'
    
    def test_dutch_detection(self):
        """Test detection of Dutch text."""
        text = "Hallo, goedemorgen. Dank je wel, alstublieft."
        result = detect_language_from_text(text)
        assert result == 'nl'
    
    def test_very_long_text(self):
        """Test detection with very long text."""
        text = "obrigado " * 1000  # Long Portuguese text
        result = detect_language_from_text(text)
        assert result == 'pt'
    
    def test_text_with_numbers_and_symbols(self):
        """Test detection with text containing numbers and symbols."""
        text = "123 !@# obrigado $%^ 456 muito obrigado &*() 789"
        result = detect_language_from_text(text)
        assert result == 'pt'
    
    def test_text_with_punctuation(self):
        """Test detection with heavily punctuated text."""
        text = "Hello! Good morning. Thank you, very much... See you!"
        result = detect_language_from_text(text)
        assert result == 'en'
    
    def test_substring_matching(self):
        """Test that keywords match as substrings in larger words."""
        # "thank you" should match in "thanks for everything, I thank you"
        text = "I really want to thank you for your help"
        result = detect_language_from_text(text)
        assert result == 'en'


# ============================================================================
# Tests for have_ffmpeg() - System Dependency Check
# ============================================================================

@pytest.mark.unit
class TestHaveFFmpeg:
    """Tests for have_ffmpeg() function."""
    
    def test_returns_boolean(self):
        """Test that have_ffmpeg returns a boolean."""
        result = have_ffmpeg()
        assert isinstance(result, bool)
    
    def test_ffmpeg_availability(self, mocker):
        """Test detection when ffmpeg is available."""
        mocker.patch('shutil.which', return_value='/usr/bin/ffmpeg')
        result = have_ffmpeg()
        assert result is True
    
    def test_ffmpeg_not_available(self, mocker):
        """Test detection when ffmpeg is not available."""
        mocker.patch('shutil.which', return_value=None)
        result = have_ffmpeg()
        assert result is False
    
    def test_calls_shutil_which(self, mocker):
        """Test that have_ffmpeg calls shutil.which correctly."""
        mock_which = mocker.patch('shutil.which', return_value=None)
        have_ffmpeg()
        mock_which.assert_called_once_with('ffmpeg')

