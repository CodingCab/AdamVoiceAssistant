#!/usr/bin/env python3
"""
Minimum length filter preprocessor.
Filters out very short transcriptions and punctuation-only text.
"""

from typing import Dict
from utils.timing import log


class MinimumLengthFilter:
    """Filters out very short or punctuation-only transcriptions."""

    def __init__(self, config: dict = None, logger=None):
        """
        Initialize minimum length filter.

        Args:
            config: Configuration dictionary with filter settings
            logger: Optional logger instance
        """
        self.config = config or {}
        self.logger = logger

        # Filter settings
        self.min_length = self.config.get('min_text_length', 2)
        self.punctuation = '.,:;!?-—'

    def should_filter(self, text: str) -> bool:
        """
        Determine if text should be filtered out.

        Args:
            text: Text to check

        Returns:
            True if text should be filtered (removed), False otherwise
        """
        if not text or not text.strip():
            return True

        # Remove all punctuation and whitespace
        text_without_punct = text
        for punct in self.punctuation:
            text_without_punct = text_without_punct.replace(punct, '')
        text_without_punct = text_without_punct.strip()

        # Check if remaining text is too short
        if len(text_without_punct) <= self.min_length:
            log(f"Filtering out short/punctuation-only text: '{text}'", debug_only=True)
            return True

        return False

    def set_min_length(self, length: int):
        """Update the minimum length threshold."""
        self.min_length = length

    def __repr__(self):
        return f"MinimumLengthFilter(min_length={self.min_length})"
