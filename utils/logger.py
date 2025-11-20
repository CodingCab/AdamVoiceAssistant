#!/usr/bin/env python3
"""
Centralized logging system for the voice assistant.
"""

import logging
import logging.handlers
import os
from datetime import datetime
import json

class StructuredLogger:
    """Structured logging with file and console output."""

    def __init__(self, name, log_dir="logs", level=logging.INFO, debug=False):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.debug_mode = debug

        # Create logs directory
        os.makedirs(log_dir, exist_ok=True)

        # Console handler - simple format like original
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler - daily rotation
        log_file = os.path.join(log_dir, f"voice_assistant_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def debug(self, msg, **kwargs):
        """Log debug message."""
        self.logger.debug(msg, extra=kwargs)

    def info(self, msg, **kwargs):
        """Log info message."""
        self.logger.info(msg, extra=kwargs)

    def warning(self, msg, **kwargs):
        """Log warning message."""
        self.logger.warning(msg, extra=kwargs)

    def error(self, msg, **kwargs):
        """Log error message."""
        self.logger.error(msg, extra=kwargs)

    def critical(self, msg, **kwargs):
        """Log critical message."""
        self.logger.critical(msg, extra=kwargs)

    def log_event(self, event_type, action, duration=None, **metadata):
        """Log structured event with metadata."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'action': action,
            'duration': duration,
            **metadata
        }
        self.logger.info(f"EVENT: {json.dumps(event)}")
        return event


def get_logger(name, **kwargs):
    """Get or create a logger instance."""
    return StructuredLogger(name, **kwargs)
