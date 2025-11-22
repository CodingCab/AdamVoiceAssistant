#!/usr/bin/env python3
"""
Automatically record a test audio sample for benchmarking (no user prompt).
"""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from core.audio_recorder import AudioRecorder
from utils.config_manager import ConfigManager

def main():
    # Load configuration
    config_file = Path(__file__).parent / 'config' / 'config.json'
    config_manager = ConfigManager(str(config_file))
    audio_config = config_manager.get('audio')

    # Set up output file
    output_file = "test_sample.wav"

    print("Starting recording... Speak now!")
    print("Recording will stop automatically after 2 seconds of silence.")

    # Create recorder with adjusted settings for longer recording
    audio_config['min_recording_time'] = 1.0
    audio_config['silence_duration'] = 2.0
    audio_config['max_silence_timeout'] = 15.0

    recorder = AudioRecorder(audio_config)

    success = recorder.record_until_silence(output_file)

    if success:
        print(f"\nRecording saved: {output_file}")
        return 0
    else:
        print("\nRecording failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
