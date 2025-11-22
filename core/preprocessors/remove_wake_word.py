#!/usr/bin/env python3
"""
Remove wake word preprocessor.
Removes wake word from transcription text and cleans up punctuation.
"""

from typing import Tuple
from utils.timing import log


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

    def remove(self, text: str) -> Tuple[bool, str]:
        """
        Remove wake word from text if present.

        Args:
            text: Text to process

        Returns:
            Tuple of (was_removed, cleaned_text)
        """
        if not self.wake_words:
            return False, text

        text_lower = text.lower()

        # Check which wake word (if any) the text starts with
        matched_wake_word = None
        for wake_word in self.wake_words:
            if text_lower.startswith(wake_word):
                matched_wake_word = wake_word
                break

        if not matched_wake_word:
            return False, text

        # Remove wake word from text
        remaining_text = text[len(matched_wake_word):].lstrip()

        # Remove leading punctuation (comma, dot, etc.) left from transcription
        remaining_text = remaining_text.lstrip('.,;:!? ')

        # If only punctuation remains, return empty
        if not remaining_text or remaining_text.strip() in '.,;:!?':
            log("Wake word removed but only punctuation remains, returning empty", debug_only=True)
            return True, ""

        log(f"Wake word '{matched_wake_word}' removed, cleaned text: '{remaining_text}'", debug_only=True)
        return True, remaining_text

    def set_wake_words(self, wake_words: list):
        """Update the wake words list."""
        self.wake_words = [w.lower() for w in wake_words]

    def __repr__(self):
        return f"RemoveWakeWord(wake_words={self.wake_words})"
