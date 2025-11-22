#!/usr/bin/env python3
"""
Record a test audio sample for benchmarking.
"""

import sys
import json
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

    print("=" * 60)
    print("RECORDING TEST SAMPLE")
    print("=" * 60)
    print("\nI will record approximately 10 seconds of audio.")
    print("Please speak naturally when you hear 'Sound detected!'")
    print("The recording will stop automatically after 2 seconds of silence.\n")
    print("Press Enter to start recording...")
    input()

    # Create recorder with adjusted settings for longer recording
    audio_config['min_recording_time'] = 1.0
    audio_config['silence_duration'] = 2.0
    audio_config['max_silence_timeout'] = 10.0

    recorder = AudioRecorder(audio_config)

    def on_sound_detected():
        print("\n🎤 Sound detected! Recording...")

    def on_silence_detected():
        print("🔇 Silence detected, stopping...")

    success = recorder.record_until_silence(
        output_file,
        on_sound_detected=on_sound_detected,
        on_silence_detected=on_silence_detected
    )

    if success:
        print(f"\n✅ Recording saved: {output_file}")
        print("\nYou can now run the benchmark script to test different models.")
    else:
        print("\n❌ Recording failed")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
