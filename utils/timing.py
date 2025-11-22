#!/usr/bin/env python3
"""
Global timing utilities for delta time tracking across the application.
Shows time elapsed since the LAST log message (not since command start).
"""

import time
import sys

# Last log time - updated after each log message
LAST_LOG_TIME = time.time()

# Debug mode - set by the application
DEBUG_MODE = False

def set_debug_mode(debug: bool):
    """Set debug mode globally."""
    global DEBUG_MODE
    DEBUG_MODE = debug

def get_elapsed() -> float:
    """Get elapsed time in seconds since last log message."""
    return time.time() - LAST_LOG_TIME

def format_elapsed() -> str:
    """Get formatted elapsed time string [X.XXs]."""
    return f"[{get_elapsed():.2f}s]"

def reset_timer():
    """Reset the timer (updates last log time to now)."""
    global LAST_LOG_TIME
    LAST_LOG_TIME = time.time()

def log(message: str, debug_only: bool = False) -> None:
    """
    Standard logging procedure - print message with timing prefix.
    Shows time since LAST log message, then updates the timer.

    Args:
        message: Message to log
        debug_only: If True, only show in debug mode
    """
    global LAST_LOG_TIME

    # Skip debug-only messages if not in debug mode
    if debug_only and not DEBUG_MODE:
        return

    # Get elapsed time since last log
    elapsed = time.time() - LAST_LOG_TIME

    # Update last log time to now
    LAST_LOG_TIME = time.time()

    # Print with delta time
    msg = f"[{elapsed:.2f}s] {message}"
    print(msg, flush=True)
