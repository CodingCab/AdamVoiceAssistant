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

from utils.timing import format_elapsed, log

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
        self.silence_threshold_ratio = config.get('silence_threshold_ratio', 0.90)
        self.min_recording_time = config.get('min_recording_time', 0.5)
        self.max_silence_timeout = config.get('max_silence_timeout', 5.0)
        self.buffer_size = config.get('buffer_size', 43)

    def _is_silent(self, audio_data: bytes, threshold: int) -> bool:
        """Check if audio data is below the silence threshold using RMS."""
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        # Use RMS (root mean square) instead of mean - better for audio energy
        rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
        return rms < threshold

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
            # Use a sliding window equal to silence_duration to check for consistent silence
            recent_chunks = []
            debug_counter = 0
            rms_history = []  # Track last 10 RMS levels for averaging

            while True:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
                total_chunks += 1

                # Calculate current audio level using RMS
                audio_array = np.frombuffer(data, dtype=np.int16)
                audio_level = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))

                # Track RMS history (last 10 values)
                rms_history.append(audio_level)
                if len(rms_history) > 10:
                    rms_history.pop(0)

                # Calculate average and ratio for dynamic silence detection
                avg_rms = sum(rms_history) / len(rms_history) if rms_history else audio_level
                rms_ratio = audio_level / avg_rms if avg_rms > 0 else 1.0

                # Combined silence detection: must meet BOTH criteria to be considered sound
                # 1. Absolute threshold: audio level must be above minimum
                # 2. Adaptive ratio: current level must be significantly above recent average (1.5x)
                is_chunk_silent = (audio_level < self.silence_threshold) or (rms_ratio < 1.5)

                # Debug output every 20 chunks (~0.5 seconds)
                debug_counter += 1
                if debug_counter % 20 == 0:
                    log(f"RMS level: {audio_level:.0f} (avg10: {avg_rms:.0f}, ratio: {rms_ratio:.2f}, threshold: {self.silence_threshold}) - {'SILENT' if is_chunk_silent else 'SOUND'}", debug_only=True)

                # Track recent chunks in a sliding window matching silence_duration
                recent_chunks.append(is_chunk_silent)

                # Keep window size equal to silence_duration
                if len(recent_chunks) > chunks_needed_for_silence:
                    recent_chunks.pop(0)

                # Once we have a full window, check if enough of it is silent
                if len(recent_chunks) >= chunks_needed_for_silence and total_chunks >= min_chunks:
                    silent_ratio = sum(recent_chunks) / len(recent_chunks)
                    if silent_ratio >= self.silence_threshold_ratio:
                        log(f"Silence detected (ratio: {silent_ratio:.2f}), stopping recording...")  # Always show
                        if on_silence_detected:
                            on_silence_detected()
                        break

                # Also check max timeout in case of extended silence
                if len(recent_chunks) >= chunks_needed_for_silence:
                    silent_ratio = sum(recent_chunks) / len(recent_chunks)
                    if silent_ratio >= self.silence_threshold_ratio:
                        if len(recent_chunks) * self.chunk_size / self.sample_rate >= self.max_silence_timeout:
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

                log(f"Saved audio: {os.path.basename(output_filename)} ({duration:.1f}s, {file_size} bytes)", debug_only=True)

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
