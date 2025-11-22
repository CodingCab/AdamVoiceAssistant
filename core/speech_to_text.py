#!/usr/bin/env python3
"""
Speech recognition component using Faster-Whisper.
Modular refactoring of the original transcribe_audio.py
"""

import os
import sys
import json
import time
import wave
from typing import Dict, Optional, Tuple
from pathlib import Path

from utils.timing import format_elapsed, log

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None


class SpeechToText:
    """Converts audio to text using Faster-Whisper."""

    def __init__(self, config: dict, logger=None):
        """
        Initialize speech recognizer.

        Args:
            config: Dictionary containing transcription configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize Whisper model with configuration."""
        if WhisperModel is None:
            if self.logger:
                self.logger.error("faster-whisper not installed. Install with: pip install faster-whisper")
            return

        try:
            model_name = self.config.get('model', 'tiny')
            device = self.config.get('device', 'cpu')
            compute_type = self.config.get('compute_type', 'float32')
            cpu_threads = self.config.get('cpu_threads', 4)

            log(f"Loading Whisper model: {model_name} ({compute_type})", debug_only=True)

            # Fix OpenMP library conflict on macOS
            os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

            self.model = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
                cpu_threads=cpu_threads,
                num_workers=1
            )

            log("Whisper model loaded successfully", debug_only=True)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load Whisper model: {e}")
            raise

    def _get_audio_duration(self, audio_filename: str) -> float:
        """Get duration of audio file in seconds."""
        try:
            with wave.open(audio_filename, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
                return duration
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not get audio duration: {e}")
            return 0.0

    def transcribe(self, audio_filename: str) -> Optional[Dict]:
        """
        Transcribe audio file to text.

        Args:
            audio_filename: Path to audio file

        Returns:
            Dictionary with transcription data or None on error
        """
        if not self.model:
            if self.logger:
                self.logger.error("Model not initialized")
            return None

        if not os.path.exists(audio_filename):
            if self.logger:
                self.logger.error(f"Audio file not found: {audio_filename}")
            return None

        try:
            start_time = time.time()
            audio_duration = self._get_audio_duration(audio_filename)

            log(f"Transcribing: {os.path.basename(audio_filename)} ({audio_duration:.1f}s)", debug_only=True)

            # Build transcription parameters
            transcribe_params = {
                'audio': audio_filename,
                'language': self.config.get('language', 'en'),
                'beam_size': self.config.get('beam_size', 1),
                'vad_filter': self.config.get('vad_filter', False),
                'word_timestamps': True,
                'temperature': self.config.get('temperature', 0),
                'condition_on_previous_text': self.config.get('condition_on_previous_text', True),
                'no_speech_threshold': self.config.get('no_speech_threshold', 0.6),
                'log_prob_threshold': self.config.get('logprob_threshold', -1.0),
                'compression_ratio_threshold': self.config.get('compression_ratio_threshold', 2.4)
            }

            # Add initial prompt if configured (helps with context and vocabulary)
            initial_prompt = self.config.get('initial_prompt', '')
            if initial_prompt:
                transcribe_params['initial_prompt'] = initial_prompt

            # Add hotwords if configured (boosts specific words)
            hotwords = self.config.get('hotwords', '')
            if hotwords:
                transcribe_params['hotwords'] = hotwords

            # Transcribe audio with word timestamps enabled
            segments, info = self.model.transcribe(**transcribe_params)

            # Collect transcription and segment details
            segments_list = list(segments)
            transcription = " ".join([segment.text for segment in segments_list]).strip()
            transcription_time = time.time() - start_time

            if not transcription:
                log("No transcription found (empty audio)", debug_only=True)
                return None

            # Collect detailed segment information
            segment_details = []
            for segment in segments_list:
                segment_info = {
                    'start': round(segment.start, 2),
                    'end': round(segment.end, 2),
                    'text': segment.text,
                    'avg_logprob': round(segment.avg_logprob, 4),
                    'no_speech_prob': round(segment.no_speech_prob, 4),
                    'compression_ratio': round(segment.compression_ratio, 2)
                }

                # Add word timestamps if available
                if hasattr(segment, 'words') and segment.words:
                    segment_info['words'] = [
                        {
                            'word': word.word,
                            'start': round(word.start, 2),
                            'end': round(word.end, 2),
                            'probability': round(word.probability, 4)
                        }
                        for word in segment.words
                    ]

                segment_details.append(segment_info)

            # Build result data with all available information
            result = {
                'filename': os.path.basename(audio_filename),
                'filepath': audio_filename,
                'recording_length_seconds': round(audio_duration, 2),
                'transcription_time_seconds': round(transcription_time, 2),
                'transcription': transcription,
                'language': info.language,
                'language_probability': round(info.language_probability, 2),
                'duration': round(info.duration, 2),
                'duration_after_vad': round(info.duration_after_vad, 2) if hasattr(info, 'duration_after_vad') else None,
                'all_language_probs': {lang: round(prob, 4) for lang, prob in (info.all_language_probs or [])} if hasattr(info, 'all_language_probs') else None,
                'segments': segment_details,
                'total_segments': len(segment_details)
            }

            log(f"Transcription complete: \n    {transcription}")  # Always show

            return result

        except Exception as e:
            if self.logger:
                self.logger.error(f"Transcription error: {e}")
            return None

    def transcribe_and_save(self, audio_filename: str) -> Optional[str]:
        """
        Transcribe audio file and save to JSON.

        Args:
            audio_filename: Path to audio file

        Returns:
            Path to JSON output file or None on error
        """
        result = self.transcribe(audio_filename)

        if not result:
            return None

        # Save to JSON file
        json_filename = audio_filename.replace('.wav', '.json')

        try:
            with open(json_filename, 'w') as f:
                json.dump(result, f, indent=2)

            log(f"Saved transcription: {json_filename}", debug_only=True)

            return json_filename

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save transcription: {e}")
            return None

    def detect_language(self, audio_filename: str) -> Optional[Tuple[str, float]]:
        """
        Detect language of audio file.

        Args:
            audio_filename: Path to audio file

        Returns:
            Tuple of (language_code, confidence) or None on error
        """
        if not self.model or not os.path.exists(audio_filename):
            return None

        try:
            segments, info = self.model.transcribe(
                audio_filename,
                language=None,  # Let model detect
                beam_size=1
            )

            return (info.language, info.language_probability)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Language detection error: {e}")
            return None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass
