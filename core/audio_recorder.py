#!/usr/bin/env python3
"""
Audio recording component with silence detection.
Modular refactoring of the original record_with_silence_detection.py
"""

import pyaudio
import wave
import numpy as np
import os
import sys
import time
from datetime import datetime
from typing import Optional, Callable
from pathlib import Path

from timing import format_elapsed, log

class AudioRecorder:
    """Records audio with automatic silence detection."""

    def __init__(self, config: dict, logger=None):
        """
        Initialize audio recorder with configuration.

        Args:
            config: Dictionary containing audio configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger
        self.stream = None
        self.audio = None
        self.is_recording = False

        # Audio parameters
        self.sample_rate = config.get('sample_rate', 44100)
        self.channels = config.get('channels', 1)
        format_val = config.get('format', '16')
        if isinstance(format_val, str):
            format_val = format_val.replace('int', '')
        self.format = getattr(pyaudio, f"paInt{format_val}")
        self.chunk_size = config.get('chunk_size', 1024)
        self.silence_threshold = config.get('silence_threshold', 700)
        self.silence_duration = config.get('silence_duration', 1.0)
        self.min_recording_time = config.get('min_recording_time', 0.5)
        self.max_silence_timeout = config.get('max_silence_timeout', 5.0)
        self.buffer_size = config.get('buffer_size', 43)

    def _is_silent(self, audio_data: bytes, threshold: int) -> bool:
        """Check if audio data is below the silence threshold."""
        return np.abs(np.frombuffer(audio_data, dtype=np.int16)).mean() < threshold

    def record_until_silence(
        self,
        output_filename: str,
        on_recording_start: Optional[Callable] = None,
        on_sound_detected: Optional[Callable] = None,
        on_silence_detected: Optional[Callable] = None,
    ) -> bool:
        """
        Record audio until silence is detected.

        Args:
            output_filename: Path to save audio file
            on_recording_start: Callback when recording starts
            on_sound_detected: Callback when sound is detected
            on_silence_detected: Callback when silence is detected

        Returns:
            True if recording was successful, False otherwise
        """
        record_start_time = time.time()
        self.is_recording = True

        try:
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )

            frames = []
            buffer = []
            silent_chunks = 0
            chunks_needed_for_silence = int((self.sample_rate / self.chunk_size) * self.silence_duration)
            min_chunks = int((self.sample_rate / self.chunk_size) * self.min_recording_time)
            total_chunks = 0
            recording_started = False
            silence_start_time = time.time()

            log("Waiting for sound...", debug_only=True)

            # Phase 1: Wait for speech to start
            while not recording_started:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                buffer.append(data)

                if len(buffer) > self.buffer_size:
                    buffer.pop(0)

                if not self._is_silent(data, self.silence_threshold):
                    log("Sound detected! Recording...")  # Always show
                    if on_sound_detected:
                        on_sound_detected()

                    recording_started = True
                    frames.extend(buffer)
                    total_chunks = len(buffer)

                    if on_recording_start:
                        on_recording_start()

                else:
                    total_chunks += 1
                    if time.time() - silence_start_time >= self.max_silence_timeout:
                        return False

            # Phase 2: Record until silence is detected
            while True:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
                total_chunks += 1

                if self._is_silent(data, self.silence_threshold):
                    silent_chunks += 1
                    if silent_chunks * self.chunk_size / self.sample_rate >= self.max_silence_timeout:
                        break
                else:
                    silent_chunks = 0

                if silent_chunks >= chunks_needed_for_silence and total_chunks >= min_chunks:
                    log("Silence detected, stopping recording...")  # Always show
                    if on_silence_detected:
                        on_silence_detected()
                    break

            # Save audio file
            if frames:
                Path(output_filename).parent.mkdir(parents=True, exist_ok=True)

                with wave.open(output_filename, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.audio.get_sample_size(self.format))
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(frames))

                duration = len(frames) * self.chunk_size / self.sample_rate
                file_size = os.path.getsize(output_filename)

                log(f"Saved audio: {output_filename} ({duration:.1f}s, {file_size} bytes)", debug_only=True)

                return True

            return False

        except KeyboardInterrupt:
            log("Recording interrupted by user", debug_only=True)
            raise

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during recording: {e}")
            return False

        finally:
            self.is_recording = False
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.audio:
                self.audio.terminate()

    def stop(self):
        """Stop recording."""
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
