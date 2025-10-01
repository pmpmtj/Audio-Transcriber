# Audio Transcription Package

A modular Python package for transcribing audio files using OpenAI's Whisper API with optional language detection capabilities.

## Features

- 🎵 **Multiple Audio Formats**: Support for MP3, M4A, and WAV files
- 🌍 **Language Detection**: Keyword-based language routing with ffmpeg probe sampling
- ⚡ **Fast Processing**: Configurable probe sampling for quick language detection
- 🔧 **Modular Design**: Clean separation between business logic and CLI interface
- 📦 **Installable Package**: Easy installation and distribution via pip
- ⚙️ **Configurable**: Centralized configuration management
- 🎯 **Multiple Interfaces**: CLI, library, and extensible for web APIs

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API key
- FFmpeg (optional, for probe sampling)
- python-dotenv (optional, for .env file support)

### Quick Install

**Install from source (development):**
```bash
git clone <repository-url>
cd audio-transcriber
pip install -e .
```

**Install for production:**
```bash
pip install .
```

**Set up your OpenAI API key:**

**Option 1: Environment variable**
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key-here"

# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
```

**Option 2: .env file (recommended for development)**
```bash
# Install python-dotenv for .env support
pip install python-dotenv

# Create .env file
cp .env.example .env
# Edit .env and add your API key
```

## Quick Start

### CLI Usage

After installation, use the `transcribe-audio` command:

**Basic transcription:**
```bash
transcribe-audio input.m4a
```

**With language routing (recommended):**
```bash
transcribe-audio input.mp3 --language-routing
```

**Force specific language:**
```bash
transcribe-audio input.wav --language pt
```

**Save to file:**
```bash
transcribe-audio input.m4a --out transcript.json
```

**Dry run (cost estimation):**
```bash
transcribe-audio input.m4a --dry-run --language-routing
```

**Batch processing from stdin:**
```bash
# Process multiple files
echo -e "file1.mp3\nfile2.m4a\nfile3.wav" | transcribe-audio --stdin --language-routing

# Process all audio files in a directory
find /path/to/audio -name "*.mp3" | transcribe-audio --stdin --out-dir /path/to/output
```

**Alternative CLI usage (if not installed):**
```bash
python -m transcribe_audio.cli.transcribe_cli input.m4a
```

### Library Usage

**Basic usage:**
```python
from transcribe_audio import transcribe_audio

# Simple transcription
result = transcribe_audio("audio.mp3")
print(result['text'])
```

**Advanced usage with options:**
```python
from transcribe_audio import transcribe_audio

result = transcribe_audio(
    audio_path="audio.m4a",
    language_routing=True,
    probe_seconds=15,
    model="gpt-4o-transcribe",
    temperature=0.0
)

# Access transcription and metadata
text = result['text']
metadata = result['_meta']
print(f"Detected language: {metadata['routed_language']}")
```

**Configuration access:**
```python
from transcribe_audio import TranscriptionConfig

# Get model settings
main_model = TranscriptionConfig.get_model('main')
detect_model = TranscriptionConfig.get_model('detect')

# Get defaults
temperature = TranscriptionConfig.get_default('temperature')
probe_seconds = TranscriptionConfig.get_default('probe_seconds')
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `audio_path` | Path to audio file (MP3/M4A/WAV) | Required |
| `--model` | Main transcription model | `gpt-4o-transcribe` |
| `--detect-model` | Language detection model | `gpt-4o-mini-transcribe` |
| `--language` | Force specific language (ISO-639-1) | Auto-detect |
| `--probe-seconds` | Seconds to sample for detection | `25` |
| `--no-probe` | Disable ffmpeg probe sampling | `False` |
| `--language-routing` | Enable keyword-based routing | `False` |
| `--out` | Output JSON file path | Print to stdout |
| `--temperature` | Decoding temperature (0.0-1.0) | `0.0` |
| `--dry-run` | Show what would be done without API calls | `False` |
| `--stdin` | Read file paths from stdin for batch processing | `False` |

## Supported Languages

The package supports keyword-based detection for:

- **Portuguese** (pt)
- **Spanish** (es) 
- **English** (en)
- **French** (fr)
- **German** (de)
- **Italian** (it)
- **Dutch** (nl)
- **Russian** (ru)
- **Chinese** (zh)
- **Japanese** (ja)

## Configuration

All configuration is centralized in `transcribe_audio/config/transcription_config.py`:

```python
from transcribe_audio import TranscriptionConfig

# Access models
main_model = TranscriptionConfig.get_model('main')
detect_model = TranscriptionConfig.get_model('detect')

# Access defaults
temperature = TranscriptionConfig.get_default('temperature')
probe_seconds = TranscriptionConfig.get_default('probe_seconds')

# Check supported extensions
is_allowed = TranscriptionConfig.is_extension_allowed('.mp3')
```

### Customizing Language Keywords

Edit the `LANGUAGE_KEYWORDS` dictionary in `transcription_config.py` to add or modify language detection keywords.

## Integration Examples

### Web API Integration

```python
from flask import Flask, request, jsonify
from transcribe_audio import transcribe_audio

app = Flask(__name__)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio_file = request.files['audio']
    
    # Save temporarily
    temp_path = f"temp_{audio_file.filename}"
    audio_file.save(temp_path)
    
    try:
        result = transcribe_audio(temp_path, language_routing=True)
        return jsonify({
            'success': True,
            'transcription': result['text'],
            'language': result['_meta']['routed_language']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        os.remove(temp_path)
```

### Batch Processing

```python
import os
import json
from pathlib import Path
from transcribe_audio import transcribe_audio

def batch_transcribe(input_dir, output_dir):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    for audio_file in input_path.glob("*.mp3"):
        try:
            result = transcribe_audio(str(audio_file), language_routing=True)
            
            # Save with same name but .json extension
            output_file = output_path / f"{audio_file.stem}.json"
            output_file.write_text(json.dumps(result, indent=2))
            
            print(f"Processed: {audio_file.name}")
        except Exception as e:
            print(f"Error processing {audio_file.name}: {e}")

# Usage
batch_transcribe("input_audio/", "output_transcripts/")
```

## Error Handling

The package uses structured exit codes:

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Usage/argument error |
| `2` | File not found/unsupported type |
| `3` | API error (network/auth/model) |
| `4` | FFmpeg error (non-fatal) |

**Exception types for library usage:**
- `ImportError`: OpenAI SDK not installed
- `FileNotFoundError`: Audio file doesn't exist
- `ValueError`: Unsupported file type

## Development

### Project Structure

```
audio-transcriber/
├── pyproject.toml              # Package configuration
├── README.md                   # This file
├── requirements.txt            # Dependencies
├── transcribe_audio/           # Main package
│   ├── __init__.py            # Package exports
│   ├── cli/                   # CLI interface
│   │   └── transcribe_cli.py  # CLI implementation
│   ├── config/                # Configuration
│   │   └── transcription_config.py
│   ├── core/                  # Business logic
│   │   ├── transcription.py   # Main transcription function
│   │   └── language_detection.py # Language detection
│   └── logging_utils/         # Logging configuration
├── examples/                   # Usage examples
│   ├── example_usage.py       # Sample code
│   └── input.m4a             # Test audio file
└── tests/                     # Test suite
```

### Running Tests

```bash
# Install in development mode
pip install -e .

# Run tests
pytest

# Test imports
python -c "from transcribe_audio import transcribe_audio; print('Package OK')"

# Test CLI help
transcribe-audio --help
```

### Extending the Package

**Adding new interfaces:**
```python
# Create your own interface
from transcribe_audio import transcribe_audio

def my_custom_interface(audio_path, **options):
    # Your custom logic here
    result = transcribe_audio(audio_path, **options)
    # Your custom processing here
    return result
```

**Development setup:**
```bash
# Clone and install in development mode
git clone <repository-url>
cd audio-transcriber
pip install -e .

# Run tests
pytest

# Build package
python -m build
```

## Troubleshooting

### Common Issues

**1. OpenAI API Key not set:**
```
ERROR: OPENAI_API_KEY is not set. Set it and retry.
```
**Solution:** Set the environment variable with your OpenAI API key.

**2. FFmpeg not found:**
```
WARNING: ffmpeg failed to create probe slice
```
**Solution:** Install FFmpeg or use `--no-probe` flag to disable probe sampling.

**3. Unsupported file type:**
```
ERROR: Unsupported file type '.flac'. Use: .m4a, .mp3, .wav
```
**Solution:** Convert your audio file to MP3, M4A, or WAV format.

**4. Import errors:**
```
ERROR: Failed to import OpenAI SDK
```
**Solution:** Install dependencies with `pip install -r requirements.txt`

### Performance Tips

- Use `--language-routing` for better accuracy with known languages
- Adjust `--probe-seconds` based on your audio length (shorter for quick detection)
- Use `gpt-4o-mini-transcribe` for detection to save costs
- Set `--temperature 0.0` for consistent, deterministic results

## License

This project is open source. Please check the license file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the configuration options
3. Test with a simple audio file first
4. Check OpenAI API status and quotas
