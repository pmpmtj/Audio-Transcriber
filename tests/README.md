# Test Suite for transcribe_audio Package

This directory contains comprehensive unit and integration tests for the transcribe_audio package.

## Test Structure

Tests are organized to mirror the source code structure:

```
tests/
├── conftest.py                          # Shared fixtures and pytest configuration
├── test_config/
│   └── test_transcription_config.py     # Tests for configuration module
├── test_core/
│   ├── test_language_detection.py       # Tests for pure language detection functions
│   ├── test_language_detection_mocked.py # Tests with mocked dependencies
│   └── test_transcription.py            # Tests for transcription functions
├── test_cli/
│   └── test_transcribe_cli.py          # Tests for CLI functions
└── test_logging_utils/
    └── test_logging_config.py          # Tests for logging utilities
```

## Running Tests

### Install Test Dependencies

```powershell
pip install -r requirements.txt
```

This installs:
- `pytest` - Test framework
- `pytest-mock` - Mocking utilities
- `pytest-cov` - Coverage reporting

### Run All Tests

```powershell
pytest
```

### Run Specific Test File

```powershell
pytest tests/test_config/test_transcription_config.py
```

### Run Specific Test Class

```powershell
pytest tests/test_core/test_language_detection.py::TestDetectLanguageFromText
```

### Run Specific Test Function

```powershell
pytest tests/test_core/test_language_detection.py::TestDetectLanguageFromText::test_detect_portuguese
```

### Run with Verbose Output

```powershell
pytest -v
```

### Run with Coverage Report

```powershell
pytest --cov=transcribe_audio --cov-report=html
```

Then open `htmlcov/index.html` in your browser to view detailed coverage.

### Run Only Unit Tests

```powershell
pytest -m unit
```

### Run Only Integration Tests

```powershell
pytest -m integration
```

### Run Tests that Don't Require FFmpeg

```powershell
pytest -m "not requires_ffmpeg"
```

## Test Markers

Tests are marked with the following categories:

- **`@pytest.mark.unit`** - Pure unit tests with no external dependencies
- **`@pytest.mark.integration`** - Integration tests with mocked external dependencies
- **`@pytest.mark.slow`** - Tests that take significant time to run
- **`@pytest.mark.requires_ffmpeg`** - Tests that require FFmpeg installed
- **`@pytest.mark.requires_api_key`** - Tests that require OpenAI API key

## Test Coverage

Current test coverage goal: **80%**

### Coverage by Module

To see coverage breakdown by module:

```powershell
pytest --cov=transcribe_audio --cov-report=term-missing
```

This will show which lines are not covered by tests.

## Writing New Tests

### Test File Naming

- Test files must start with `test_`
- Test classes must start with `Test`
- Test functions must start with `test_`

### Using Fixtures

Common fixtures are defined in `conftest.py`:

```python
def test_my_function(sample_audio_path, mock_openai_client):
    """Test description."""
    # Test code here
```

Available fixtures:
- `temp_dir` - Temporary directory
- `sample_audio_path` - Fake MP3 file
- `sample_m4a_path` - Fake M4A file
- `sample_wav_path` - Fake WAV file
- `mock_openai_client` - Mocked OpenAI client
- `mock_api_key` - Sets fake API key
- `portuguese_text`, `spanish_text`, `english_text` - Sample texts for language detection

### Mocking Example

```python
def test_with_mock(mocker, sample_audio_path):
    """Test with mocked dependency."""
    mock_func = mocker.patch('module.function_name')
    mock_func.return_value = "expected value"
    
    # Your test code
    result = my_function()
    
    assert mock_func.called
    assert result == "expected value"
```

### Testing Exceptions

```python
def test_raises_error():
    """Test that function raises expected error."""
    with pytest.raises(ValueError) as exc_info:
        dangerous_function()
    
    assert "error message" in str(exc_info.value)
```

## Continuous Integration

To run tests in CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=transcribe_audio --cov-fail-under=80
```

## Test Best Practices

1. **One assertion per test** (when possible)
2. **Descriptive test names** that explain what is being tested
3. **AAA pattern** - Arrange, Act, Assert
4. **Mock external dependencies** (API calls, file I/O, subprocess)
5. **Clean up resources** in fixtures using `yield`
6. **Use parametrize** for testing multiple inputs:

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "en"),
    ("olá", "pt"),
    ("hola", "es"),
])
def test_detection(input, expected):
    assert detect_language_from_text(input) == expected
```

## Troubleshooting

### Tests Pass Locally But Fail in CI

- Check that all dependencies are installed
- Verify environment variables are set
- Check for hardcoded paths (use fixtures instead)

### Coverage is Lower Than Expected

- Run with `--cov-report=html` to see what's not covered
- Add tests for edge cases and error paths
- Check if certain code paths are unreachable

### Mocks Not Working

- Verify the import path in `mocker.patch()`
- Use `mocker.patch.object()` for class methods
- Check that mocks are set up before the tested code runs

### Fixture Not Found

- Check that fixture is defined in `conftest.py` or the test file
- Verify fixture name matches exactly
- Make sure pytest can find `conftest.py`

## Debugging Tests

### Run with Print Statements

```powershell
pytest -s
```

The `-s` flag shows print statements and logs.

### Run with PDB Debugger

```powershell
pytest --pdb
```

Drops into debugger on first failure.

### Run Last Failed Tests Only

```powershell
pytest --lf
```

## Updating Tests

When making changes to the codebase:

1. Update relevant tests to match new behavior
2. Add new tests for new functionality
3. Run full test suite before committing
4. Verify coverage hasn't decreased

```powershell
# Check coverage before changes
pytest --cov=transcribe_audio --cov-report=term

# Make changes

# Check coverage after changes
pytest --cov=transcribe_audio --cov-report=term
```

