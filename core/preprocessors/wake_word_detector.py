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

        # Wake word settings - support both single wake_word and multiple wake_words
        wake_words_list = self.config.get('wake_words', [])
        single_wake_word = self.config.get('wake_word', '')

        # Build list of wake words
        if wake_words_list:
            self.wake_words = [w.lower() for w in wake_words_list]
        elif single_wake_word:
            self.wake_words = [single_wake_word.lower()]
        else:
            self.wake_words = []

        self.cooldown_duration = self.config.get('wake_word_cooldown', 15)

    def detect(self, text: str) -> bool:
        """
        Detect if any wake word is present in text.

        Args:
            text: Text to check for wake word

        Returns:
            True if any wake word detected, False otherwise
        """
        if not self.wake_words:
            return False

        text_lower = text.lower()

        # Check if text starts with any wake word
        for wake_word in self.wake_words:
            if text_lower.startswith(wake_word):
                log(f"Wake word '{wake_word}' detected", debug_only=True)
                return True

        return False

    def get_cooldown_duration(self) -> int:
        """
        Get the cooldown duration in seconds.

        Returns:
            Cooldown duration in seconds
        """
        return self.cooldown_duration

    def set_wake_words(self, wake_words: list):
        """Update the wake words list."""
        self.wake_words = [w.lower() for w in wake_words]

    def set_cooldown_duration(self, duration: int):
        """Update the cooldown duration."""
        self.cooldown_duration = duration

    def __repr__(self):
        return f"WakeWordDetector(wake_words={self.wake_words}, cooldown={self.cooldown_duration}s)"
