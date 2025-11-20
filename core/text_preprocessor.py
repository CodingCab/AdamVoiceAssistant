#!/usr/bin/env python3
"""
Text preprocessing component.
Processes transcribed text before pasting.
Handles: punctuation, capitalization, word corrections, echo detection, etc.
"""

import re
import os
from typing import Dict, Optional, Tuple

from timing import log
from .preprocessors import WakeWordDetector, RemoveWakeWord, MinimumLengthFilter


class TextPreprocessor:
    """Preprocesses transcribed text for pasting."""

    def __init__(self, config: dict, logger=None):
        """
        Initialize text preprocessor.

        Args:
            config: Dictionary containing feature configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger
        self.last_spoken_file = None
        self.last_spoken_text = None
        self.correction_rules = self._load_correction_rules()

        # Initialize preprocessors
        self.wake_word_detector = WakeWordDetector(config, logger)
        self.wake_word_remover = RemoveWakeWord(config, logger)
        self.length_filter = MinimumLengthFilter(config, logger)

    def _load_correction_rules(self) -> Dict[str, str]:
        """Load text correction rules (can be extended)."""
        return {
            # Common speech-to-text mistakes
            'gonna': 'going to',
            'wanna': 'want to',
            'gotta': 'got to',
            'kinda': 'kind of',
            'sorta': 'sort of',
        }

    def set_last_spoken_file(self, filepath: str):
        """Set the file that contains the last spoken text."""
        self.last_spoken_file = filepath
        self._load_last_spoken()

    def _load_last_spoken(self):
        """Load last spoken text from file."""
        if self.last_spoken_file and os.path.exists(self.last_spoken_file):
            try:
                with open(self.last_spoken_file, 'r') as f:
                    self.last_spoken_text = f.read().strip().lower()
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Could not load last spoken text: {e}")
                self.last_spoken_text = None

    def detect_echo(self, transcription: str) -> bool:
        """
        Detect if transcription is an echo of system response.

        Args:
            transcription: Text to check

        Returns:
            True if echo detected, False otherwise
        """
        if not self.config.get('echo_detection', True):
            return False

        if not self.last_spoken_text:
            return False

        # Normalize both texts
        normalized_transcription = self._normalize(transcription)
        normalized_last_spoken = self._normalize(self.last_spoken_text)

        # Check for similarity
        similarity = self._calculate_similarity(normalized_transcription, normalized_last_spoken)

        if self.logger and similarity > 0.7:
            self.logger.info(f"Echo detected (similarity: {similarity:.2f})")

        return similarity > 0.7

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text

    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0-1)."""
        # Simple implementation using intersection over union
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 1.0 if text1 == text2 else 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def apply_corrections(self, text: str) -> str:
        """
        Apply text correction rules.

        Args:
            text: Text to correct

        Returns:
            Corrected text
        """
        if not text:
            return text

        for mistake, correction in self.correction_rules.items():
            # Use word boundaries to avoid partial replacements
            pattern = r'\b' + mistake + r'\b'
            text = re.sub(pattern, correction, text, flags=re.IGNORECASE)

        return text

    def fix_capitalization(self, text: str) -> str:
        """
        Fix capitalization in text.

        Args:
            text: Text to fix

        Returns:
            Text with proper capitalization
        """
        if not text:
            return text

        # Capitalize first letter of sentence
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()

        # Capitalize after periods, question marks, exclamation marks
        text = re.sub(
            r'([.!?]\s+)([a-z])',
            lambda m: m.group(1) + m.group(2).upper(),
            text
        )

        return text

    def fix_punctuation(self, text: str) -> str:
        """
        Fix common punctuation issues.

        Args:
            text: Text to fix

        Returns:
            Text with fixed punctuation
        """
        if not text:
            return text

        # Add period if missing
        if text and text[-1] not in '.!?':
            text += '.'

        # Remove spaces before punctuation
        text = re.sub(r'\s+([.!?,;:])', r'\1', text)

        # Add space after punctuation
        text = re.sub(r'([.!?,;:])(?!\s|$)', r'\1 ', text)

        return text

    def preprocess(
        self,
        transcription: str,
        apply_corrections: bool = True,
        fix_capitalization: bool = True,
        fix_punctuation: bool = True,
        detect_echo: bool = True,
    ) -> Tuple[str, Dict]:
        """
        Apply all preprocessing steps.

        Args:
            transcription: Raw transcribed text
            apply_corrections: Whether to apply correction rules
            fix_capitalization: Whether to fix capitalization
            fix_punctuation: Whether to fix punctuation
            detect_echo: Whether to check for echo

        Returns:
            Tuple of (processed_text, metadata_dict)
        """
        metadata = {
            'original': transcription,
            'echo_detected': False,
            'corrections_applied': 0,
            'wake_word_detected': False,
        }

        # Check for echo first
        if detect_echo and self.detect_echo(transcription):
            metadata['echo_detected'] = True
            log("Echo detected, skipping processing", debug_only=True)
            return "", metadata

        # Check if transcription should be filtered (too short or punctuation-only)
        if self.length_filter.should_filter(transcription):
            return "", metadata

        # Check for wake word
        wake_word_detected = self.wake_word_detector.detect(transcription)
        metadata['wake_word_detected'] = wake_word_detected

        # Remove wake word if detected
        if wake_word_detected:
            _, transcription = self.wake_word_remover.remove(transcription)

        # If wake word was detected but no text remains, return empty
        if wake_word_detected and not transcription:
            return "", metadata

        # Apply corrections
        if apply_corrections:
            original_length = len(transcription.split())
            transcription = self.apply_corrections(transcription)
            new_length = len(transcription.split())
            metadata['corrections_applied'] = original_length - new_length

        # Fix capitalization
        if fix_capitalization:
            transcription = self.fix_capitalization(transcription)

        # Fix punctuation
        if fix_punctuation:
            transcription = self.fix_punctuation(transcription)

        metadata['processed'] = transcription

        return transcription, metadata

    def add_correction_rule(self, mistake: str, correction: str):
        """Add custom correction rule."""
        self.correction_rules[mistake] = correction

    def __repr__(self):
        return f"TextPreprocessor(rules={len(self.correction_rules)})"
