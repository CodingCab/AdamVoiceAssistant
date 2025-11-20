#!/usr/bin/env python3
"""
State management system for tracking assistant state and mode.
"""

from enum import Enum
from typing import Dict, List, Any
from datetime import datetime
import json

class AssistantMode(Enum):
    """Operating modes for the voice assistant."""
    DICTATION = "dictation"      # Auto-paste transcriptions
    COMMAND = "command"          # Respond to voice commands
    CONVERSATION = "conversation" # Multi-turn conversation
    PAUSED = "paused"           # Paused, not recording


class AssistantState(Enum):
    """Assistant runtime states."""
    IDLE = "idle"              # Waiting for user input
    LISTENING = "listening"    # Actively recording
    PROCESSING = "processing"  # Transcribing/processing
    SPEAKING = "speaking"      # TTS response
    ERROR = "error"            # Error state
    STOPPED = "stopped"        # Shutdown


class StateManager:
    """Manages application state and history."""

    def __init__(self, max_history: int = 100):
        self.mode = AssistantMode.DICTATION
        self.state = AssistantState.IDLE
        self.settings = {
            'echo_detection': True,
            'auto_paste': True,
            'language': 'en',
        }
        self.history: List[Dict[str, Any]] = []
        self.max_history = max_history
        self.session_start = datetime.now()
        self.stats = {
            'total_recordings': 0,
            'total_transcriptions': 0,
            'successful_pastes': 0,
            'errors': 0,
        }

    def set_mode(self, mode: AssistantMode):
        """Set the operating mode."""
        self.mode = mode

    def set_state(self, state: AssistantState):
        """Set the current state."""
        self.state = state

    def get_mode(self) -> AssistantMode:
        """Get current mode."""
        return self.mode

    def get_state(self) -> AssistantState:
        """Get current state."""
        return self.state

    def set_setting(self, key: str, value: Any):
        """Set a configuration setting."""
        self.settings[key] = value

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting."""
        return self.settings.get(key, default)

    def add_to_history(self, transcription: str, metadata: Dict = None):
        """Add transcription to history."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'transcription': transcription,
            'mode': self.mode.value,
            'metadata': metadata or {}
        }
        self.history.append(entry)

        # Keep history size bounded
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get last N entries from history."""
        return self.history[-limit:]

    def clear_history(self):
        """Clear all history."""
        self.history = []

    def get_last_transcription(self) -> str:
        """Get the last transcription."""
        if self.history:
            return self.history[-1]['transcription']
        return None

    def increment_stat(self, stat_name: str, amount: int = 1):
        """Increment a statistics counter."""
        if stat_name in self.stats:
            self.stats[stat_name] += amount

    def get_stats(self) -> Dict:
        """Get all statistics."""
        session_duration = (datetime.now() - self.session_start).total_seconds()
        return {
            **self.stats,
            'session_duration_seconds': session_duration,
            'current_mode': self.mode.value,
            'current_state': self.state.value,
        }

    def reset_stats(self):
        """Reset all statistics."""
        self.stats = {
            'total_recordings': 0,
            'total_transcriptions': 0,
            'successful_pastes': 0,
            'errors': 0,
        }

    def to_dict(self) -> Dict:
        """Convert state to dictionary."""
        return {
            'mode': self.mode.value,
            'state': self.state.value,
            'settings': self.settings,
            'history_size': len(self.history),
            'stats': self.get_stats(),
        }

    def __repr__(self):
        return f"StateManager(mode={self.mode.value}, state={self.state.value})"
