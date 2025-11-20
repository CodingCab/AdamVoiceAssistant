#!/usr/bin/env python3
"""
Text pasting component.
Automatically pastes transcribed text into the active window.
"""

import time
from typing import Optional

from timing import log

try:
    import pyperclip
    import pyautogui
except ImportError:
    pyperclip = None
    pyautogui = None


class TextPaster:
    """Pastes text into the active application window."""

    def __init__(self, config: dict, logger=None):
        """
        Initialize text paster.

        Args:
            config: Dictionary containing paste configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger

        if pyperclip is None or pyautogui is None:
            if self.logger:
                self.logger.error("pyperclip or pyautogui not installed")

    def paste_text(self, text: str) -> bool:
        """
        Paste text into active window.

        Args:
            text: Text to paste

        Returns:
            True if successful, False otherwise
        """
        if not text or not text.strip():
            if self.logger:
                self.logger.warning("Cannot paste empty text")
            return False

        if pyperclip is None or pyautogui is None:
            if self.logger:
                self.logger.error("Clipboard or keyboard automation not available")
            return False

        try:
            # Stash existing clipboard content
            original_clipboard = pyperclip.paste()
            log("Clipboard content stashed.", debug_only=True)

            # Copy to clipboard
            pyperclip.copy(text)
            log("Copied to clipboard", debug_only=True)
            if self.logger:
                self.logger.debug("Text copied to clipboard")

            # Wait for clipboard to update
            delay_before = self.config.get('delay_before_paste', 0.2)
            time.sleep(delay_before)

            # Ensure clean keyboard state before pasting
            pyautogui.keyUp('command')
            pyautogui.keyUp('v')
            time.sleep(0.05)

            # Paste using keyboard (Cmd+V)
            pyautogui.hotkey('command', 'v')
            log("Pasted from clipboard", debug_only=True)

            if self.logger:
                self.logger.debug("Text pasted (Cmd+V)")

            # Wait after paste
            delay_after = self.config.get('delay_after_paste', 0.1)
            time.sleep(delay_after)

            # Send Enter if configured
            if self.config.get('send_enter', True):
                pyautogui.press('enter')
                if self.logger:
                    self.logger.debug("Pressed Enter")

            # Restore original clipboard content
            pyperclip.copy(original_clipboard)
            log("Restored content clipboard", debug_only=True)

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to paste text: {e}")
            return False

    def paste_from_file(self, json_filename: str) -> bool:
        """
        Paste transcription from JSON file.

        Args:
            json_filename: Path to JSON transcription file

        Returns:
            True if successful, False otherwise
        """
        import json
        import os

        if not os.path.exists(json_filename):
            if self.logger:
                self.logger.error(f"JSON file not found: {json_filename}")
            return False

        try:
            with open(json_filename, 'r') as f:
                data = json.load(f)

            transcription = data.get('transcription', '').strip()

            if not transcription:
                if self.logger:
                    self.logger.warning("No transcription found in JSON file")
                return False

            return self.paste_text(transcription)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error reading JSON file: {e}")
            return False

    def copy_to_clipboard(self, text: str) -> bool:
        """
        Copy text to clipboard without pasting.

        Args:
            text: Text to copy

        Returns:
            True if successful, False otherwise
        """
        if not text:
            return False

        if pyperclip is None:
            if self.logger:
                self.logger.error("pyperclip not available")
            return False

        try:
            pyperclip.copy(text)
            log(f"Text copied to clipboard: '{text}'", debug_only=True)
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to copy to clipboard: {e}")
            return False

    def __repr__(self):
        return "TextPaster()"
