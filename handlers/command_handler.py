#!/usr/bin/env python3
"""
Voice command handler.
Processes voice commands and executes corresponding actions.
"""

from typing import Callable, Dict, Optional, Any
from utils import CommandsManager
from timing import log


class CommandHandler:
    """Handles voice command recognition and execution."""

    def __init__(self, commands_manager: CommandsManager, logger=None):
        """
        Initialize command handler.

        Args:
            commands_manager: CommandsManager instance
            logger: Optional logger instance
        """
        self.commands_manager = commands_manager
        self.logger = logger
        self.action_handlers: Dict[str, Callable] = {}

    def register_action(self, action: str, handler: Callable):
        """
        Register action handler.

        Args:
            action: Action name
            handler: Callable that handles the action
        """
        self.action_handlers[action] = handler
        if self.logger and hasattr(self.logger, 'debug'):
            self.logger.debug(f"Registered action handler: {action}")

    def process_transcription(self, transcription: str) -> Optional[Dict[str, Any]]:
        """
        Process transcription as potential command.

        Args:
            transcription: User transcription text

        Returns:
            Result dictionary or None if not a command
        """
        # Try to match as command
        command = self.commands_manager.get_command(transcription)

        if not command:
            if self.logger and hasattr(self.logger, 'debug'):
                self.logger.debug(f"No command matched: '{transcription}'")
            return None

        command_name = command.get('name')
        action = command.get('action')

        log(f"Command detected: {command_name} (action: {action})")

        # Execute action
        return self.execute_action(action, command, transcription)

    def execute_action(self, action: str, command: Dict, transcription: str) -> Dict[str, Any]:
        """
        Execute command action.

        Args:
            action: Action name
            command: Full command dictionary
            transcription: Original transcription

        Returns:
            Action result dictionary
        """
        result = {
            'command': command.get('name'),
            'action': action,
            'success': False,
            'response': None,
        }

        # Check if handler is registered
        if action not in self.action_handlers:
            if self.logger and hasattr(self.logger, 'warning'):
                self.logger.warning(f"No handler for action: {action}")
            result['response'] = f"No handler for action: {action}"
            return result

        try:
            # Execute handler
            handler = self.action_handlers[action]
            response = handler(command, transcription)

            result['success'] = True
            result['response'] = response

            log(f"Action executed successfully: {action}")

        except Exception as e:
            if self.logger and hasattr(self.logger, 'error'):
                self.logger.error(f"Error executing action {action}: {e}")
            result['response'] = f"Error: {str(e)}"

        return result

    def is_command(self, transcription: str) -> bool:
        """
        Check if transcription is a recognized command.

        Args:
            transcription: Text to check

        Returns:
            True if recognized as command, False otherwise
        """
        return self.commands_manager.get_command(transcription) is not None

    def __repr__(self):
        return f"CommandHandler(handlers={len(self.action_handlers)})"
