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

# Try to import analytics module if available
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from analytics import log_run
except ImportError:
    # Analytics module not available, define a no-op function
    def log_run(*args, **kwargs):
        pass

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
LAST_SPOKEN_FILE = os.path.join(CACHE_DIR, 'last_spoken.txt')

def save_last_spoken(text):
    """Save the last spoken text to a file."""
    try:
        # Create cache directory if it doesn't exist
        os.makedirs(CACHE_DIR, exist_ok=True)
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

def get_system_speech_rate():
    """Get speech rate from macOS Accessibility settings."""
    try:
        result = subprocess.run(
            ['defaults', 'read', 'com.apple.Accessibility', 'SpokenContentDefaultVoiceSelectionsByLanguage'],
            capture_output=True, text=True
        )
        # Parse rate from output (format: rate = 1.5;)
        import re
        match = re.search(r'rate\s*=\s*([0-9.]+)', result.stdout)
        if match:
            # Convert system rate (0-2 multiplier) to words per minute
            # System rate 1.0 = 175 wpm (default), 2.0 = 350 wpm, 0.5 = 87 wpm
            system_rate = float(match.group(1))
            return int(175 * system_rate)
    except:
        pass
    return None  # Use default if can't read

def speak(text):
    """Speak text using macOS say command in background."""
    if not text or not text.strip():
        return

    try:
        # Save what we're about to say
        save_last_spoken(text)

        # Mute microphone input before speaking
        mute_microphone()

        # Use macOS built-in 'say' command in background
        # Rate: 193 wpm (10% faster than default 175 wpm)
        subprocess.Popen(['say', '-r', '193', text])

        # Schedule unmuting after a delay (approximate speech duration)
        # Estimate: ~150 words per minute, ~2.5 chars per word = ~6 chars per second
        estimated_duration = len(text) / 6.0 + 1.0  # Add 1 second buffer

        # Run unmute in background after estimated duration
        subprocess.Popen([
            'bash', '-c',
            f'sleep {estimated_duration:.1f} && osascript -e "set volume input volume 100"'
        ])

        # Log analytics immediately (won't capture actual duration, but that's ok)
        log_run('speak', 'speak', duration=0, additional_data={'text_length': len(text)})

    except FileNotFoundError:
        print("Error: 'say' command not found (macOS only)")
        unmute_microphone()
        log_run('speak', 'speak', duration=0, additional_data={'error': 'FileNotFoundError'})

if __name__ == "__main__":
    # Get the text to speak
    if len(sys.argv) > 1:
        # Text provided as argument
        text = ' '.join(sys.argv[1:])
    else:
        # Read from stdin
        text = sys.stdin.read().strip()
        if not text:
            print("Usage: python3 speak.py \"text to speak\"")
            print("   or: echo \"text\" | python3 speak.py")
            sys.exit(1)

    # Fork to background immediately so parent can exit
    pid = os.fork()

    if pid > 0:
        # Parent process - exit immediately
        sys.exit(0)

    # Child process continues - detach from parent
    os.setsid()

    # Execute speech in background
    speak(text)
