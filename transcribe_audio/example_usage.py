#!/usr/bin/env python3
"""
Example usage of the transcribe_audio package.

This demonstrates how to use the transcription functionality as a library
in your own applications.
"""

import os
from pathlib import Path

# Import the main transcription function
from src.core import transcribe_audio


def main():
    """Example usage of the transcription library."""
    
    # Ensure API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Example audio file path (adjust as needed)
    audio_file = Path(__file__).parent / "src" / "input.m4a"
    
    if not audio_file.exists():
        print(f"Audio file not found: {audio_file}")
        print("Please place an audio file (MP3, M4A, or WAV) in the src directory")
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
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
