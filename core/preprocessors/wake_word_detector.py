#!/usr/bin/env python3
"""
Wake word detection preprocessor.
Detects wake word in transcription text.
"""

from typing import Dict
from timing import log


class WakeWordDetector:
    """Detects wake word in transcription."""

    def __init__(self, config: dict = None, logger=None):
        """
        Initialize wake word detector.

        Args:
            config: Configuration dictionary with wake word settings
            logger: Optional logger instance
        """
        self.config = config or {}
        self.logger = logger

        # Wake word settings
        self.wake_word = self.config.get('wake_word', '').lower()
        self.cooldown_duration = self.config.get('wake_word_cooldown', 15)

    def detect(self, text: str) -> bool:
        """
        Detect if wake word is present in text.

        Args:
            text: Text to check for wake word

        Returns:
            True if wake word detected, False otherwise
        """
        if not self.wake_word:
            return False

        text_lower = text.lower()

        # Check if text starts with wake word
        if text_lower.startswith(self.wake_word):
            log(f"Wake word '{self.wake_word}' detected", debug_only=True)
            return True

        return False

    def get_cooldown_duration(self) -> int:
        """
        Get the cooldown duration in seconds.

        Returns:
            Cooldown duration in seconds
        """
        return self.cooldown_duration

    def set_wake_word(self, wake_word: str):
        """Update the wake word."""
        self.wake_word = wake_word.lower()

    def set_cooldown_duration(self, duration: int):
        """Update the cooldown duration."""
        self.cooldown_duration = duration

    def __repr__(self):
        return f"WakeWordDetector(wake_word='{self.wake_word}', cooldown={self.cooldown_duration}s)"
