#!/usr/bin/env python3
"""
Text-to-speech script using macOS built-in 'say' command.

Usage:
  python3 speak.py "Hello, this is a test"
  echo "Hello world" | python3 speak.py
"""

import sys
import subprocess
import os
import time

# Add parent directory to path to find analytics module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from analytics import log_run

LAST_SPOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last_spoken.txt')

def save_last_spoken(text):
    """Save the last spoken text to a file."""
    try:
        with open(LAST_SPOKEN_FILE, 'w') as f:
            f.write(text.strip().lower())
    except:
        pass

def mute_microphone():
    """Mute the input device using osascript."""
    try:
        subprocess.run([
            'osascript', '-e',
            'set volume input volume 0'
        ], check=True, capture_output=True)
    except:
        pass

def unmute_microphone():
    """Restore microphone input volume using osascript."""
    try:
        subprocess.run([
            'osascript', '-e',
            'set volume input volume 100'
        ], check=True, capture_output=True)
    except:
        pass

def speak(text):
    """Speak text using macOS say command."""
    if not text or not text.strip():
        return

    start_time = time.time()

    try:
        # Save what we're about to say
        save_last_spoken(text)

        # Mute microphone input before speaking
        mute_microphone()

        # Use macOS built-in 'say' command
        subprocess.run(['say', text], check=True)

        # Unmute microphone input after speaking
        unmute_microphone()

        # Log analytics
        duration = time.time() - start_time
        log_run('speak', 'speak', duration=duration, additional_data={'text_length': len(text)})

    except subprocess.CalledProcessError as e:
        print("Error: Could not speak text")
        # Ensure microphone is unmuted even if there's an error
        unmute_microphone()
        duration = time.time() - start_time
        log_run('speak', 'speak', duration=duration, additional_data={'error': 'CalledProcessError'})
    except FileNotFoundError:
        print("Error: 'say' command not found (macOS only)")
        # Ensure microphone is unmuted even if there's an error
        unmute_microphone()
        duration = time.time() - start_time
        log_run('speak', 'speak', duration=duration, additional_data={'error': 'FileNotFoundError'})

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Text provided as argument
        text = ' '.join(sys.argv[1:])
        speak(text)
    else:
        # Read from stdin
        text = sys.stdin.read().strip()
        if text:
            speak(text)
        else:
            print("Usage: python3 speak.py \"text to speak\"")
            print("   or: echo \"text\" | python3 speak.py")
