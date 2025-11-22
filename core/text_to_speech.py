#!/usr/bin/env python3
"""
Text-to-speech component.
Converts text to speech using macOS 'say' command.
"""

import subprocess
import os
import time
from typing import Optional

from utils.timing import log


class TextToSpeech:
    """Text-to-speech using macOS native capabilities."""

    def __init__(self, config: dict, logger=None):
        """
        Initialize speaker.

        Args:
            config: Dictionary containing speech configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger
        self.last_spoken_file = None
        self.is_macos = self._check_macos()

    def _check_macos(self) -> bool:
        """Check if running on macOS."""
        try:
            subprocess.run(['say', '--version'], capture_output=True, timeout=1)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def set_last_spoken_file(self, filepath: str):
        """Set file to save last spoken text."""
        self.last_spoken_file = filepath

    def _save_last_spoken(self, text: str):
        """Save spoken text for echo detection."""
        if not self.last_spoken_file:
            return

        try:
            with open(self.last_spoken_file, 'w') as f:
                f.write(text.strip().lower())
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not save last spoken text: {e}")

    def _mute_microphone(self) -> bool:
        """Mute microphone input."""
        try:
            mute_level = self.config.get('mute_level', 0)
            subprocess.run([
                'osascript', '-e',
                f'set volume input volume {mute_level}'
            ], check=True, capture_output=True, timeout=2)
            if self.logger:
                self.logger.debug("Microphone muted")
            return True
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not mute microphone: {e}")
            return False

    def _unmute_microphone(self) -> bool:
        """Unmute microphone input."""
        try:
            unmute_level = self.config.get('unmute_level', 100)
            subprocess.run([
                'osascript', '-e',
                f'set volume input volume {unmute_level}'
            ], check=True, capture_output=True, timeout=2)
            if self.logger:
                self.logger.debug("Microphone unmuted")
            return True
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not unmute microphone: {e}")
            return False

    def speak(self, text: str) -> bool:
        """
        Speak text using macOS 'say' command.

        Args:
            text: Text to speak

        Returns:
            True if successful, False otherwise
        """
        if not text or not text.strip():
            return False

        if not self.is_macos:
            if self.logger:
                self.logger.warning("Text-to-speech not available (not on macOS)")
            return False

        start_time = time.time()

        try:
            # Pre-speak delay to ensure recording cycle is complete
            pre_speak_delay = self.config.get('pre_speak_delay', 3)
            if pre_speak_delay > 0:
                time.sleep(pre_speak_delay)

            # Save what we're about to say
            self._save_last_spoken(text)

            # Mute microphone if configured
            mute_before_speak = self.config.get('mute_input_before_speak', True)
            if mute_before_speak:
                self._mute_microphone()

            # Speak using 'say' command
            subprocess.run(['say', text], check=True)

            log(f"Spoken: '{text}'")

            # Unmute microphone
            if mute_before_speak:
                self._unmute_microphone()

            duration = time.time() - start_time
            if self.logger:
                self.logger.debug(f"Speech duration: {duration:.2f}s")

            return True

        except subprocess.CalledProcessError as e:
            if self.logger:
                self.logger.error(f"Speech error: {e}")
            # Ensure microphone is unmuted on error
            if mute_before_speak:
                self._unmute_microphone()
            return False

        except Exception as e:
            if self.logger:
                self.logger.error(f"Unexpected speech error: {e}")
            # Ensure microphone is unmuted on error
            try:
                self._unmute_microphone()
            except:
                pass
            return False

    def speak_with_voice(self, text: str, voice: Optional[str] = None) -> bool:
        """
        Speak text using specific voice.

        Args:
            text: Text to speak
            voice: Voice identifier (e.g., 'com.apple.speech.synthesis.voice.Alex')

        Returns:
            True if successful, False otherwise
        """
        if not text or not text.strip():
            return False

        if not self.is_macos:
            if self.logger:
                self.logger.warning("Text-to-speech not available (not on macOS)")
            return False

        voice = voice or self.config.get('voice', 'Alex')

        start_time = time.time()

        try:
            # Pre-speak delay
            pre_speak_delay = self.config.get('pre_speak_delay', 3)
            if pre_speak_delay > 0:
                time.sleep(pre_speak_delay)

            # Save what we're about to say
            self._save_last_spoken(text)

            # Mute microphone
            mute_before_speak = self.config.get('mute_input_before_speak', True)
            if mute_before_speak:
                self._mute_microphone()

            # Speak with voice
            subprocess.run(['say', '-v', voice, text], check=True)

            log(f"Spoken with voice '{voice}': '{text}'")

            # Unmute microphone
            if mute_before_speak:
                self._unmute_microphone()

            duration = time.time() - start_time
            if self.logger:
                self.logger.debug(f"Speech duration: {duration:.2f}s")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Speech error: {e}")
            # Ensure microphone is unmuted on error
            if mute_before_speak:
                self._unmute_microphone()
            return False

    def list_voices(self) -> list:
        """Get list of available voices on macOS."""
        if not self.is_macos:
            return []

        try:
            result = subprocess.run(
                ['say', '-v', '?'],
                capture_output=True,
                text=True,
                timeout=5
            )
            voices = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        voices.append({
                            'name': parts[0],
                            'id': parts[0] if len(parts) == 2 else ' '.join(parts[1:-1])
                        })
            return voices
        except Exception as e:
            if self.logger:
                self.logger.error(f"Could not list voices: {e}")
            return []

    def test_speech(self) -> bool:
        """Test text-to-speech functionality."""
        log("Testing text-to-speech...")

        success = self.speak("Testing speech synthesis")

        if success:
            log("Text-to-speech test successful")

        return success

    def __repr__(self):
        return f"TextToSpeech(macos={self.is_macos})"
