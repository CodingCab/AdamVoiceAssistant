#!/usr/bin/env python3
"""
No speech detection preprocessor.
Analyzes transcription metadata to detect if the audio contains actual speech or just noise/silence.
"""

from typing import Dict, Optional
from utils.timing import log


class NoSpeechDetector:
    """Detects whether transcription contains actual speech or is likely noise/silence."""

    def __init__(self, config: dict = None, logger=None):
        """
        Initialize no speech detector.

        Args:
            config: Configuration dictionary with thresholds
            logger: Optional logger instance
        """
        self.config = config or {}
        self.logger = logger

        # Detection thresholds (can be overridden in config)
        self.no_speech_prob_threshold = self.config.get('no_speech_prob_threshold', 0.5)
        self.word_prob_threshold = self.config.get('word_prob_threshold', 0.2)
        self.compression_ratio_threshold = self.config.get('compression_ratio_threshold', 1.0)
        self.min_transcription_length = self.config.get('min_transcription_length', 3)
        self.min_avg_word_prob = self.config.get('min_avg_word_prob', 0.1)

    def is_valid_speech(self, transcription_data: Dict) -> bool:
        """
        Determine if transcription contains valid speech.

        Args:
            transcription_data: Dictionary containing transcription results

        Returns:
            True if valid speech detected, False otherwise
        """
        if not transcription_data:
            return False

        transcription = transcription_data.get('transcription', '').strip()
        segments = transcription_data.get('segments', [])

        # Check 1: Empty or very short transcription
        if len(transcription) < self.min_transcription_length:
            log(f"No speech: transcription too short ({len(transcription)} chars)", debug_only=True)
            return False

        # Check 2: Only punctuation
        if transcription.replace('.', '').replace(',', '').replace('!', '').replace('?', '').strip() == '':
            log("No speech: only punctuation detected", debug_only=True)
            return False

        # Check 3: Analyze segments
        if not segments:
            return True  # If no segment data, trust the transcription

        total_no_speech_prob = 0
        total_avg_logprob = 0
        total_compression_ratio = 0
        low_confidence_words = 0
        total_words = 0

        for segment in segments:
            # Accumulate segment-level metrics
            total_no_speech_prob += segment.get('no_speech_prob', 0)
            total_avg_logprob += segment.get('avg_logprob', 0)
            total_compression_ratio += segment.get('compression_ratio', 1)

            # Check word-level confidence
            words = segment.get('words', [])
            for word in words:
                total_words += 1
                word_prob = word.get('probability', 1)
                if word_prob < self.word_prob_threshold:
                    low_confidence_words += 1

        num_segments = len(segments)

        # Calculate averages
        avg_no_speech_prob = total_no_speech_prob / num_segments
        avg_compression_ratio = total_compression_ratio / num_segments

        # Check 4: High no_speech_prob indicates silence/noise
        if avg_no_speech_prob > self.no_speech_prob_threshold:
            log(f"No speech: high no_speech_prob ({avg_no_speech_prob:.2f})", debug_only=True)
            return False

        # Check 5: Very low compression ratio indicates gibberish
        if avg_compression_ratio < self.compression_ratio_threshold:
            log(f"No speech: low compression ratio ({avg_compression_ratio:.2f})", debug_only=True)
            return False

        # Check 6: Too many low confidence words
        if total_words > 0:
            low_confidence_ratio = low_confidence_words / total_words
            if low_confidence_ratio > 0.7:  # 70% of words have low confidence
                log(f"No speech: too many low confidence words ({low_confidence_ratio:.2%})", debug_only=True)
                return False

            # Check 7: Average word probability too low (indicates noise/gibberish)
            avg_word_prob = sum(segment.get('words', [{}])[i].get('probability', 0)
                               for segment in segments
                               for i in range(len(segment.get('words', [])))) / total_words
            if avg_word_prob < self.min_avg_word_prob:
                log(f"No speech: average word probability too low ({avg_word_prob:.4f})", debug_only=True)
                return False

        # All checks passed - valid speech detected
        return True

    def get_detection_details(self, transcription_data: Dict) -> Dict:
        """
        Get detailed analysis of speech detection.

        Args:
            transcription_data: Dictionary containing transcription results

        Returns:
            Dictionary with detection details and scores
        """
        if not transcription_data:
            return {'valid_speech': False, 'reason': 'No transcription data'}

        transcription = transcription_data.get('transcription', '').strip()
        segments = transcription_data.get('segments', [])

        details = {
            'valid_speech': False,
            'transcription_length': len(transcription),
            'num_segments': len(segments),
            'checks': {}
        }

        # Run all checks and record results
        if len(transcription) < self.min_transcription_length:
            details['checks']['length'] = {'passed': False, 'value': len(transcription)}
            details['reason'] = 'Transcription too short'
            return details
        else:
            details['checks']['length'] = {'passed': True, 'value': len(transcription)}

        # Check punctuation
        text_without_punct = transcription.replace('.', '').replace(',', '').replace('!', '').replace('?', '').strip()
        if text_without_punct == '':
            details['checks']['punctuation'] = {'passed': False}
            details['reason'] = 'Only punctuation'
            return details
        else:
            details['checks']['punctuation'] = {'passed': True}

        if segments:
            total_no_speech_prob = sum(s.get('no_speech_prob', 0) for s in segments)
            total_compression_ratio = sum(s.get('compression_ratio', 1) for s in segments)

            avg_no_speech_prob = total_no_speech_prob / len(segments)
            avg_compression_ratio = total_compression_ratio / len(segments)

            details['avg_no_speech_prob'] = round(avg_no_speech_prob, 4)
            details['avg_compression_ratio'] = round(avg_compression_ratio, 2)

            details['checks']['no_speech_prob'] = {
                'passed': avg_no_speech_prob <= self.no_speech_prob_threshold,
                'value': avg_no_speech_prob,
                'threshold': self.no_speech_prob_threshold
            }

            details['checks']['compression_ratio'] = {
                'passed': avg_compression_ratio >= self.compression_ratio_threshold,
                'value': avg_compression_ratio,
                'threshold': self.compression_ratio_threshold
            }

            # Word confidence
            total_words = 0
            low_confidence_words = 0
            for segment in segments:
                for word in segment.get('words', []):
                    total_words += 1
                    if word.get('probability', 1) < self.word_prob_threshold:
                        low_confidence_words += 1

            if total_words > 0:
                low_conf_ratio = low_confidence_words / total_words
                details['checks']['word_confidence'] = {
                    'passed': low_conf_ratio <= 0.7,
                    'low_confidence_ratio': round(low_conf_ratio, 4),
                    'total_words': total_words
                }

        # Determine if all checks passed
        all_passed = all(check.get('passed', True) for check in details['checks'].values())
        details['valid_speech'] = all_passed

        if not all_passed:
            failed_checks = [name for name, check in details['checks'].items() if not check.get('passed', True)]
            details['reason'] = f"Failed checks: {', '.join(failed_checks)}"

        return details

    def __repr__(self):
        return f"NoSpeechDetector(thresholds: no_speech={self.no_speech_prob_threshold}, compression={self.compression_ratio_threshold})"
