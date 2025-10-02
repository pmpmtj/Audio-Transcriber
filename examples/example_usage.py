#!/usr/bin/env python3
"""
Example usage of the transcribe_audio package.

This demonstrates how to use the transcription functionality as a library
in your own applications, showcasing various features and options.
"""

import os
from pathlib import Path

# Import the main transcription function and validation helper
from src.transcribe_audio import transcribe_audio, validate_audio_file


def basic_example():
    """Basic transcription example."""
    print("=== Basic Transcription Example ===")
    
    # Example audio file path (adjust as needed)
    audio_file = Path(__file__).parent / "input.m4a"
    
    if not audio_file.exists():
        print(f"Audio file not found: {audio_file}")
        print("Please place an audio file (MP3, M4A, or WAV) in the examples directory")
        return
    
    try:
        # Basic transcription
        print("Transcribing audio file...")
        result = transcribe_audio(str(audio_file))
        
        # Extract transcription text
        text = result.get('text', 'No transcription found')
        print(f"\nTranscription:\n{text}")
        
        # Show metadata
        meta = result.get('_meta', {})
        print(f"\nMetadata:")
        print(f"  Model: {meta.get('model')}")
        print(f"  Source: {meta.get('source_file')}")
        print(f"  Language routing: {meta.get('language_routing_enabled')}")
        if meta.get('routed_language'):
            print(f"  Detected language: {meta.get('routed_language')}")
        if meta.get('ffmpeg_used') is not None:
            print(f"  FFmpeg probe used: {meta.get('ffmpeg_used')}")
            
    except Exception as e:
        print(f"Error: {e}")


def advanced_example():
    """Advanced transcription example with custom options."""
    print("\n=== Advanced Transcription Example ===")
    
    audio_file = Path(__file__).parent / "input.m4a"
    
    if not audio_file.exists():
        print(f"Audio file not found: {audio_file}")
        return
    
    try:
        # Advanced transcription with custom options
        print("Transcribing with custom options...")
        result = transcribe_audio(
            audio_path=str(audio_file),
            model="gpt-4o-transcribe",  # Use main model
            detect_model="gpt-4o-mini-transcribe",  # Use probe model for detection
            language_routing=True,  # Enable language detection
            probe_seconds=30,  # Use 30-second probe for detection
            temperature=0.1,  # Slightly higher temperature for more natural output
            use_probe=True  # Enable FFmpeg probe slicing
        )
        
        # Extract transcription text
        text = result.get('text', 'No transcription found')
        print(f"\nTranscription:\n{text}")
        
        # Show detailed metadata
        meta = result.get('_meta', {})
        print(f"\nDetailed Metadata:")
        print(f"  Model: {meta.get('model')}")
        print(f"  Detection model: {meta.get('detect_model')}")
        print(f"  Source: {meta.get('source_file')}")
        print(f"  Language routing enabled: {meta.get('language_routing_enabled')}")
        print(f"  Forced language: {meta.get('forced_language')}")
        if meta.get('routed_language'):
            print(f"  Detected language: {meta.get('routed_language')}")
        if meta.get('probe_seconds'):
            print(f"  Probe seconds: {meta.get('probe_seconds')}")
        if meta.get('ffmpeg_used') is not None:
            print(f"  FFmpeg probe used: {meta.get('ffmpeg_used')}")
            
    except Exception as e:
        print(f"Error: {e}")


def validation_example():
    """Example of using the validation helper."""
    print("\n=== File Validation Example ===")
    
    audio_file = Path(__file__).parent / "input.m4a"
    
    try:
        # Validate the audio file before processing
        print(f"Validating audio file: {audio_file}")
        validated_path = validate_audio_file(str(audio_file))
        print(f"OK File is valid: {validated_path}")
        
        # Now we can safely transcribe
        print("File validation passed, proceeding with transcription...")
        
    except FileNotFoundError:
        print(f"ERROR File not found: {audio_file}")
    except ValueError as e:
        print(f"ERROR Invalid file: {e}")
    except Exception as e:
        print(f"ERROR Validation error: {e}")


def main():
    """Run all examples."""
    
    # Ensure API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        print("You can also create a .env file with: OPENAI_API_KEY=your-key-here")
        return
    
    # Run examples
    basic_example()
    advanced_example()
    validation_example()
    
    print("\n=== Example Complete ===")
    print("For more options, see the CLI usage:")
    print("  transcribe-audio --help")


if __name__ == "__main__":
    main()
