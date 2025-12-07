#!/usr/bin/env python3
"""
Single-shot voice listener - triggers the background listener.

Usage:
    python3 listen_once.py           # Wait up to 10 seconds
    python3 listen_once.py 15        # Wait up to 15 seconds

The background listener (listen.py --standby) must be running.
Returns transcribed text to stdout, or empty if no speech detected.
"""

import sys
import os
import time

app_dir = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(app_dir, '.cache')
TRIGGER_FILE = os.path.join(CACHE_DIR, '.listen_trigger')
RESULT_FILE = os.path.join(CACHE_DIR, '.listen_result')

DEFAULT_TIMEOUT = 10


def trigger_listen(timeout_seconds: int = DEFAULT_TIMEOUT) -> str:
    """
    Trigger the background listener and wait for result.

    Args:
        timeout_seconds: Max seconds to wait for speech

    Returns:
        Transcribed text, or empty string if no speech/timeout
    """
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Clean up any old result
    if os.path.exists(RESULT_FILE):
        os.remove(RESULT_FILE)

    # Create trigger file with timeout
    with open(TRIGGER_FILE, 'w') as f:
        f.write(str(timeout_seconds))

    # Wait for result (check every 100ms)
    max_wait = timeout_seconds + 10  # Extra time for processing
    start = time.time()

    while time.time() - start < max_wait:
        if os.path.exists(RESULT_FILE):
            # Read result
            with open(RESULT_FILE, 'r') as f:
                result = f.read().strip()

            # Clean up
            os.remove(RESULT_FILE)
            return result

        time.sleep(0.1)

    # Timeout - clean up trigger if still there
    if os.path.exists(TRIGGER_FILE):
        os.remove(TRIGGER_FILE)

    return ""


def main():
    # Get timeout from args
    timeout = DEFAULT_TIMEOUT
    if len(sys.argv) > 1:
        try:
            timeout = int(sys.argv[1])
        except ValueError:
            pass

    # Trigger and get result
    text = trigger_listen(timeout)

    # Output result
    if text:
        print(text)


if __name__ == "__main__":
    main()
