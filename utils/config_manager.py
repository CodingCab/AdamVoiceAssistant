#!/usr/bin/env python3
"""
Configuration management system for the voice assistant.
Loads, validates, and provides access to configuration settings.
"""

import json
import os
from typing import Any, Dict, Optional

class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = {}
        self.load()

    def load(self):
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Config file not found: {self.config_file}")

        with open(self.config_file, 'r') as f:
            self.config = json.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'audio.sample_rate')."""
        keys = key.split('.')
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_section(self, section: str) -> Dict:
        """Get entire configuration section."""
        return self.config.get(section, {})

    def save(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def reload(self):
        """Reload configuration from file."""
        self.load()

    def validate(self) -> bool:
        """Validate configuration has required sections."""
        required_sections = ['app', 'audio', 'transcription', 'paths']
        for section in required_sections:
            if section not in self.config:
                return False
        return True

    def __repr__(self):
        return f"ConfigManager(file={self.config_file})"


class CommandsManager:
    """Manages voice command configuration."""

    def __init__(self, commands_file: str):
        self.commands_file = commands_file
        self.commands = {}
        self.command_lookup = {}
        self.load()

    def load(self):
        """Load commands from JSON file."""
        if not os.path.exists(self.commands_file):
            raise FileNotFoundError(f"Commands file not found: {self.commands_file}")

        with open(self.commands_file, 'r') as f:
            data = json.load(f)
            self.commands = data.get('commands', {})

        # Build lookup table for aliases
        self._build_lookup()

    def _build_lookup(self):
        """Build command lookup table including aliases."""
        self.command_lookup = {}

        for cmd_name, cmd_data in self.commands.items():
            # Add main command
            self.command_lookup[cmd_name.lower()] = cmd_name

            # Add aliases
            if 'aliases' in cmd_data:
                for alias in cmd_data['aliases']:
                    self.command_lookup[alias.lower()] = cmd_name

    def get_command(self, text: str) -> Optional[Dict]:
        """Get command by name or alias."""
        text = text.lower().strip()

        # Try exact match first
        cmd_name = self.command_lookup.get(text)
        if cmd_name:
            return {'name': cmd_name, **self.commands[cmd_name]}

        # Try fuzzy match if enabled
        closest = self._fuzzy_match(text)
        if closest:
            cmd_name = self.command_lookup.get(closest)
            return {'name': cmd_name, **self.commands[cmd_name]}

        return None

    def _fuzzy_match(self, text: str, max_distance: int = 2) -> Optional[str]:
        """Find closest command match using Levenshtein distance."""
        min_distance = max_distance + 1
        best_match = None

        for cmd_key in self.command_lookup.keys():
            distance = self._levenshtein_distance(text, cmd_key)
            if distance < min_distance:
                min_distance = distance
                best_match = cmd_key

        return best_match if min_distance <= max_distance else None

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return CommandsManager._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def list_commands(self) -> Dict:
        """Get all available commands with descriptions."""
        return {
            name: {
                'description': cmd.get('description', 'No description'),
                'aliases': cmd.get('aliases', [])
            }
            for name, cmd in self.commands.items()
        }

    def __repr__(self):
        return f"CommandsManager(file={self.commands_file})"
