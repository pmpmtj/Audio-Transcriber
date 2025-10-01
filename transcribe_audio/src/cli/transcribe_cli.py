#!/usr/bin/env python3
"""
CLI: Transcribe an audio file (MP3/M4A/WAV) with OpenAI and output JSON,
     with optional language routing (probe first N seconds, then transcribe).

Usage:
  python -m transcribe_audio.cli.transcribe_cli input.m4a
  python -m transcribe_audio.cli.transcribe_cli input.mp3 --out transcript.json
  python -m transcribe_audio.cli.transcribe_cli input.wav --probe-seconds 15
  python -m transcribe_audio.cli.transcribe_cli input.m4a --no-probe                     # skip ffmpeg probe
  python -m transcribe_audio.cli.transcribe_cli input.mp3 --language pt                  # bypass auto, force Portuguese
  python -m transcribe_audio.cli.transcribe_cli input.mp3 --language-routing             # enable keyword-based language routing
  python -m transcribe_audio.cli.transcribe_cli input.mp3 --model gpt-4o-mini-transcribe
  python -m transcribe_audio.cli.transcribe_cli input.mp3 --debug                        # enable debug logging
  python -m transcribe_audio.cli.transcribe_cli input.mp3 --log-dir ./my_logs           # custom log directory

Exit codes:
  0 = success
  1 = usage / argument issue
  2 = file not found / unsupported type
  3 = API error (network/auth/model/etc.)
  4 = ffmpeg error (non-fatal: we will fallback automatically)
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict

# ============================================================================
# Initialize paths - handling both frozen (PyInstaller) and regular Python execution
# ============================================================================
if getattr(sys, 'frozen', False):
    # Running as compiled executable (e.g., PyInstaller)
    SCRIPT_DIR = Path(sys.executable).parent
else:
    # Running as regular Python script
    SCRIPT_DIR = Path(__file__).resolve().parent

from ..config import TranscriptionConfig
from ..core import transcribe_audio
from ...logging_utils import get_logger, set_console_level, disable_file_logging


def die(msg: str, code: int) -> "NoReturn":  # type: ignore[name-defined]
    """Print error message and exit with specified code."""
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    # Get defaults from config
    default_model = TranscriptionConfig.get_model('main')
    default_detect_model = TranscriptionConfig.get_model('detect')
    default_temperature = TranscriptionConfig.get_default('temperature')
    default_probe_seconds = TranscriptionConfig.get_default('probe_seconds')
    default_language_routing = TranscriptionConfig.get_default('language_routing')
    default_log_dir = TranscriptionConfig.LOGGING_SETTINGS['log_dir']
    
    p = argparse.ArgumentParser(description="Transcribe audio to JSON via OpenAI with optional language routing.")
    p.add_argument("audio_path", help="Path to .mp3, .m4a, or .wav file")
    p.add_argument("--model", default=default_model, help=f"Main transcription model (default: {default_model})")
    p.add_argument("--detect-model", default=default_detect_model, help=f"Probe model for language detection (default: {default_detect_model})")
    p.add_argument("--language", default=None, help="ISO-639-1 code to force (e.g., 'en', 'pt'); omit to auto-detect")
    p.add_argument("--probe-seconds", type=int, default=default_probe_seconds, help=f"Seconds to sample for language detection (default: {default_probe_seconds})")
    p.add_argument("--no-probe", action="store_true", help="Disable ffmpeg sampling; fallback to API-only language detection")
    p.add_argument("--language-routing", action="store_true", default=default_language_routing, 
                   help="Enable keyword-based language routing (default: disabled, Whisper auto-detects)")
    p.add_argument("--out", default=None, help="Optional output .json path; prints to stdout if omitted")
    p.add_argument("--temperature", type=float, default=default_temperature, help=f"Decoding temperature (default: {default_temperature})")
    p.add_argument("--debug", action="store_true", help="Enable DEBUG level logging to console (default: INFO)")
    p.add_argument("--log-dir", default=default_log_dir, help=f"Directory for log files (default: {default_log_dir})")
    p.add_argument("--enable-file-logging", action="store_true", help="Enable logging to files (disabled by default)")
    return p.parse_args()


def ensure_api_key():
    """Ensure OpenAI API key is set."""
    if not os.getenv("OPENAI_API_KEY"):
        die("OPENAI_API_KEY is not set. Set it and retry.", TranscriptionConfig.EXIT_CODES['usage_error'])


def setup_logging_from_args(args) -> 'logging.Logger':
    """
    Initialize logging based on CLI arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Configured logger instance
    """
    log_dir = Path(args.log_dir) if args.enable_file_logging else None
    console_level = 'DEBUG' if args.debug else 'INFO'
    
    # Create logger for CLI
    logger = get_logger(
        'transcribe_cli',
        log_dir=log_dir,
        console_level=console_level,
    )
    
    # Disable file logging if not requested
    if not args.enable_file_logging:
        disable_file_logging(logger)
    
    logger.debug(f"CLI started with arguments: {vars(args)}")
    logger.debug(f"Script directory: {SCRIPT_DIR}")
    logger.debug(f"Logging level: {console_level}")
    
    return logger


def perform_transcription(args, logger) -> Dict:
    """
    Perform the transcription based on CLI arguments.
    
    Args:
        args: Parsed command-line arguments
        logger: Logger instance for output
        
    Returns:
        Transcription result dictionary
        
    Raises:
        ImportError: If OpenAI SDK not installed
        FileNotFoundError: If audio file not found
        ValueError: If file type not supported
        Exception: For API and other errors
    """
    logger.info(f"Starting transcription of: {args.audio_path}")
    logger.debug(f"Model: {args.model}, Detect model: {args.detect_model}")
    logger.debug(f"Temperature: {args.temperature}, Probe seconds: {args.probe_seconds}")
    logger.debug(f"Language routing: {args.language_routing}, Forced language: {args.language}")
    logger.debug(f"Use probe: {not args.no_probe}")
    
    # Use the core transcription functionality
    result = transcribe_audio(
        audio_path=args.audio_path,
        model=args.model,
        detect_model=args.detect_model,
        language=args.language,
        probe_seconds=args.probe_seconds,
        use_probe=(not args.no_probe),
        language_routing=args.language_routing,
        temperature=args.temperature
    )
    
    logger.debug("Transcription completed successfully")
    return result


def log_language_detection_info(args, result, logger) -> None:
    """
    Log information about language detection results.
    
    Args:
        args: Parsed command-line arguments
        result: Transcription result dictionary
        logger: Logger instance for output
    """
    if args.language_routing and not args.language:
        detected = result.get("_meta", {}).get("routed_language")
        if detected:
            logger.info(f"Language routing enabled: detected '{detected}'")
        else:
            logger.info("Language routing enabled but detection failed; Whisper will auto-detect.")
    elif not args.language:
        logger.info("Language routing disabled; Whisper will auto-detect language.")


def output_transcription_result(result, output_path, logger) -> None:
    """
    Output transcription result to file or stdout.
    
    Args:
        result: Transcription result dictionary
        output_path: Optional output file path (None for stdout)
        logger: Logger instance for output
    """
    logger.debug("Preparing output...")
    output = json.dumps(result, ensure_ascii=False, indent=2)
    
    if output_path:
        out_path = Path(output_path).expanduser().resolve()
        logger.debug(f"Writing output to: {out_path}")
        out_path.write_text(output, encoding="utf-8")
        logger.info(f"Wrote JSON transcription to: {out_path}")
    else:
        logger.debug("Writing output to stdout")
        print(output)


def main():
    """Main CLI entry point."""
    args = parse_args()
    
    # Initialize logging
    logger = setup_logging_from_args(args)
    
    # Validate environment
    logger.debug("Checking for OPENAI_API_KEY...")
    ensure_api_key()
    logger.debug("API key found")

    try:
        # Perform transcription
        result = perform_transcription(args, logger)
        
        # Log language detection info
        log_language_detection_info(args, result, logger)

    except (ImportError, FileNotFoundError, ValueError) as e:
        # Handle known errors with appropriate exit codes
        if isinstance(e, ImportError):
            logger.error(f"Import error: {e}")
            die(str(e), TranscriptionConfig.EXIT_CODES['usage_error'])
        elif isinstance(e, FileNotFoundError):
            logger.error(f"File not found: {e}")
            die(str(e), TranscriptionConfig.EXIT_CODES['file_error'])
        elif isinstance(e, ValueError):
            logger.error(f"Value error: {e}")
            die(str(e), TranscriptionConfig.EXIT_CODES['file_error'])
    except Exception as e:
        # Handle API and other errors
        logger.error(f"Transcription failed: {e}", exc_info=args.debug)
        die(f"Transcription request failed: {e}", TranscriptionConfig.EXIT_CODES['api_error'])

    # Output results
    output_transcription_result(result, args.out, logger)
    
    logger.info("Transcription process completed successfully")
    logger.debug("Exiting with success code")


if __name__ == "__main__":
    main()

