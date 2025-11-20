#!/usr/bin/env python3
"""
Remove wake word preprocessor.
Removes wake word from transcription text and cleans up punctuation.
"""

from typing import Tuple
from timing import log


class RemoveWakeWord:
    """Removes wake word from transcription text."""

    def __init__(self, config: dict = None, logger=None):
        """
        Initialize remove wake word preprocessor.

        Args:
            config: Configuration dictionary with wake word settings
            logger: Optional logger instance
        """
        self.config = config or {}
        self.logger = logger

        # Wake word settings
        self.wake_word = self.config.get('wake_word', '').lower()

    def remove(self, text: str) -> Tuple[bool, str]:
        """
        Remove wake word from text if present.

        Args:
            text: Text to process

        Returns:
            Tuple of (was_removed, cleaned_text)
        """
        if not self.wake_word:
            return False, text

        text_lower = text.lower()

        # Check if text starts with wake word
        if not text_lower.startswith(self.wake_word):
            return False, text

        # Remove wake word from text
        remaining_text = text[len(self.wake_word):].lstrip()

        # Remove leading punctuation (comma, dot, etc.) left from transcription
        remaining_text = remaining_text.lstrip('.,;:!? ')

        # If only punctuation remains, return empty
        if not remaining_text or remaining_text.strip() in '.,;:!?':
            log("Wake word removed but only punctuation remains, returning empty", debug_only=True)
            return True, ""

        log(f"Wake word removed, cleaned text: '{remaining_text}'", debug_only=True)
        return True, remaining_text

    def set_wake_word(self, wake_word: str):
        """Update the wake word."""
        self.wake_word = wake_word.lower()

    def __repr__(self):
        return f"RemoveWakeWord(wake_word='{self.wake_word}')"
