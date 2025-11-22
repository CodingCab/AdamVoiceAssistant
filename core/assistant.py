#!/usr/bin/env python3
"""
Adam Voice Assistant v2.0
A modular, production-ready voice recognition and dictation system.

Features:
- Audio recording with silence detection
- Speech-to-text transcription (Whisper)
- Text preprocessing (corrections, capitalization, punctuation)
- Auto-paste to active application
- Voice command support
- Text-to-speech responses
- Multiple operating modes
- Comprehensive logging
- Configurable settings
"""

import sys
import os
import json
import time
import fcntl
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.timing import log, set_debug_mode

from utils import get_logger, ConfigManager, CommandsManager
from core import (
    AudioRecorder,
    SpeechToText,
    TextPreprocessor,
    TextPaster,
    TextToSpeech,
    StateManager,
    AssistantMode,
    AssistantState,
)
from handlers import CommandHandler


class VoiceAssistant:
    """Main voice assistant application."""

    def __init__(self, config_dir: str = "config"):
        """
        Initialize voice assistant.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir
        self.logger = None
        self.config_manager = None
        self.commands_manager = None
        self.state_manager = None

        # Core components
        self.recorder = None
        self.recognizer = None
        self.preprocessor = None
        self.paster = None
        self.speaker = None
        self.command_handler = None

        # Session data
        self.session_start = time.time()
        self.recording_count = 0
        self.last_json_file = None
        self.last_audio_file = None

        # Wake word cooldown
        self.wake_word_active_until = 0  # Timestamp until wake word is active

        # Continuation detection
        self.last_paste_time = 0  # Timestamp of last paste

        # Initialize
        self._initialize()

    def _initialize(self):
        """Initialize all components."""
        # Load configuration
        config_path = os.path.join(self.config_dir, "config.json")
        self.config_manager = ConfigManager(config_path)

        # Set debug mode globally
        debug_mode = self.config_manager.get("app.debug", False)
        set_debug_mode(debug_mode)

        # Setup logger
        log_level = "DEBUG" if debug_mode else "INFO"
        self.logger = get_logger(
            "VoiceAssistant",
            log_dir="logs",
            debug=debug_mode
        )

        # Validate configuration
        if not self.config_manager.validate():
            raise RuntimeError("Invalid configuration")

        # Create directories
        self._create_directories()

        # Load commands
        commands_path = os.path.join(self.config_dir, "commands.json")
        self.commands_manager = CommandsManager(commands_path)

        # Initialize state manager
        self.state_manager = StateManager(max_history=100)

        # Initialize core components
        self._init_core_components()

        # Setup command handlers
        self._setup_command_handlers()

    def _create_directories(self):
        """Create necessary directories."""
        dirs = [
            self.config_manager.get("paths.recordings_dir"),
            self.config_manager.get("paths.analytics_dir"),
            self.config_manager.get("paths.cache_dir"),
            "logs",
        ]

        for dir_path in dirs:
            if dir_path:
                Path(dir_path).mkdir(parents=True, exist_ok=True)

    def _init_core_components(self):
        """Initialize all core components."""
        # Audio Recorder
        self.recorder = AudioRecorder(
            self.config_manager.get_section("audio"),
            logger=self.logger
        )

        # Speech to Text
        self.recognizer = SpeechToText(
            self.config_manager.get_section("transcription"),
            logger=self.logger
        )

        # Text Preprocessor
        self.preprocessor = TextPreprocessor(
            self.config_manager.get_section("features"),
            logger=self.logger
        )
        # Set last spoken file for echo detection
        last_spoken_file = os.path.join(
            self.config_manager.get("paths.cache_dir"),
            "last_spoken.txt"
        )
        self.preprocessor.set_last_spoken_file(last_spoken_file)

        # Text Paster
        self.paster = TextPaster(
            self.config_manager.get_section("paste"),
            logger=self.logger
        )

        # Text to Speech
        self.speaker = TextToSpeech(
            self.config_manager.get_section("speech"),
            logger=self.logger
        )
        self.speaker.set_last_spoken_file(last_spoken_file)

        # Command Handler
        self.command_handler = CommandHandler(
            self.commands_manager,
            logger=self.logger
        )

    def _setup_command_handlers(self):
        """Setup action handlers for commands."""
        self.command_handler.register_action("stop", self._handle_stop)
        self.command_handler.register_action("pause", self._handle_pause)
        self.command_handler.register_action("resume", self._handle_resume)
        self.command_handler.register_action("show_help", self._handle_help)
        self.command_handler.register_action("show_status", self._handle_status)
        self.command_handler.register_action("show_settings", self._handle_settings)
        self.command_handler.register_action("clear_cache", self._handle_clear_cache)
        self.command_handler.register_action("toggle_echo", self._handle_toggle_echo)
        self.command_handler.register_action("toggle_auto_paste", self._handle_toggle_auto_paste)
        self.command_handler.register_action("set_language", self._handle_set_language)
        self.command_handler.register_action("set_mode", self._handle_set_mode)
        self.command_handler.register_action("show_history", self._handle_show_history)
        self.command_handler.register_action("undo_last", self._handle_undo_last)
        self.command_handler.register_action("repeat_last", self._handle_repeat_last)
        self.command_handler.register_action("paste_text", self._handle_paste_text)
        self.command_handler.register_action("reload_config", self._handle_reload_config)

    def _delete_audio_file(self, audio_file: str):
        """
        Delete an audio file and log the deletion.

        Args:
            audio_file: Path to the audio file to delete
        """
        if not audio_file or not os.path.exists(audio_file):
            return

        try:
            # Get file info before deletion
            file_size = os.path.getsize(audio_file)
            import wave
            with wave.open(audio_file, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)

            os.remove(audio_file)
            log(f"Deleted audio: {os.path.basename(audio_file)} ({duration:.1f}s, {file_size} bytes)", debug_only=True)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not delete audio file: {e}")

    def process_audio_recording(self) -> bool:
        """
        Process a single audio recording cycle.

        Returns:
            True if should continue, False if should stop
        """
        # Timer already reset - just proceed
        self.state_manager.set_state(AssistantState.LISTENING)

        # Generate filename
        output_dir = self.config_manager.get("paths.recordings_dir")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        audio_file = os.path.join(output_dir, f"{timestamp}.wav")

        # Record audio
        success = self.recorder.record_until_silence(audio_file)

        if not success:
            return True

        self.recording_count += 1
        self.state_manager.increment_stat('total_recordings')

        # Store audio file path
        self.last_audio_file = audio_file

        try:
            # Transcribe
            self.state_manager.set_state(AssistantState.PROCESSING)
            json_file = self.recognizer.transcribe_and_save(audio_file)
            if not json_file:
                log("Transcription failed", debug_only=True)
                return True

            self.last_json_file = json_file
            self.state_manager.increment_stat('total_transcriptions')

            # Read transcription
            with open(json_file, 'r') as f:
                transcription_data = json.load(f)

            transcription = transcription_data.get('transcription', '').strip()
            log(transcription, debug_only=True)

            # Preprocess text
            processed_text, metadata = self.preprocessor.preprocess(transcription)

            # Check for echo
            if metadata.get('echo_detected'):
                log("Echo detected", debug_only=True)
                return True

            # Process as command or dictation
            if self.state_manager.get_mode() == AssistantMode.COMMAND:
                return self._process_as_command(processed_text)
            else:  # DICTATION or CONVERSATION mode
                return self._process_as_dictation(processed_text, metadata)
        finally:
            # Always delete the audio file after processing
            self._delete_audio_file(self.last_audio_file)

    def _process_as_command(self, text: str) -> bool:
        """
        Process transcription as voice command.

        Args:
            text: Transcribed and processed text

        Returns:
            True if should continue, False if should stop
        """
        result = self.command_handler.process_transcription(text)

        if not result:
            return True

        # Handle command result
        if result['action'] == 'stop':
            return False

        # Speak response if available
        if result['response']:
            self.state_manager.set_state(AssistantState.SPEAKING)
            self.speaker.speak(result['response'])

        self.state_manager.set_state(AssistantState.IDLE)
        return True

    def _process_as_dictation(self, text: str, metadata: dict) -> bool:
        """
        Process transcription as dictation text.

        Args:
            text: Transcribed and processed text
            metadata: Preprocessing metadata containing wake_word_detected flag

        Returns:
            True if should continue, False if should stop
        """
        # Add to history
        self.state_manager.add_to_history(text)

        # Check for inline commands (commands within dictation)
        if self.command_handler.is_command(text):
            result = self.command_handler.process_transcription(text)
            if result['action'] == 'stop':
                return False

        # Check if wake word was detected in preprocessing or if cooldown is active
        current_time = time.time()
        wake_word_detected = metadata.get('wake_word_detected', False)
        cooldown_active = current_time < self.wake_word_active_until

        if wake_word_detected:
            # Play a quick beep when keyword is detected
            os.system('afplay /System/Library/Sounds/Hero.aiff &')
            # Activate cooldown
            cooldown_duration = self.config_manager.get('features.wake_word_cooldown', 15)
            self.wake_word_active_until = current_time + cooldown_duration

        # Process text if wake word was just detected or cooldown is still active
        if wake_word_detected or cooldown_active:
            if text:  # Only paste if there's text
                self.state_manager.set_state(AssistantState.PROCESSING)

                # Determine if we should send Enter based on continuation timeout
                continuation_timeout = self.config_manager.get('paste.continuation_timeout', 3.0)
                time_since_last_paste = current_time - self.last_paste_time
                is_continuation = (self.last_paste_time > 0 and
                                 time_since_last_paste < continuation_timeout)

                # Don't send Enter if this is a continuation
                send_enter = not is_continuation

                if is_continuation:
                    log(f"Continuation detected ({time_since_last_paste:.1f}s since last paste)", debug_only=True)

                if self.paster.paste_text(text, send_enter=send_enter):
                    self.state_manager.increment_stat('successful_pastes')
                    self.last_paste_time = time.time()  # Update last paste time
                else:
                    log("Failed to paste", debug_only=True)
                    self.state_manager.increment_stat('errors')

        self.state_manager.set_state(AssistantState.IDLE)
        return True

    # Command handlers
    def _handle_stop(self, command: dict, text: str) -> str:
        """Handle stop command."""
        self.speaker.speak("Stopping voice assistant")
        return "Stopping..."

    def _handle_pause(self, command: dict, text: str) -> str:
        """Handle pause command."""
        self.state_manager.set_state(AssistantState.IDLE)
        return "Recording paused"

    def _handle_resume(self, command: dict, text: str) -> str:
        """Handle resume command."""
        return "Resuming recording"

    def _handle_help(self, command: dict, text: str) -> str:
        """Handle help command."""
        commands = self.commands_manager.list_commands()
        help_text = "Available commands: " + ", ".join(commands.keys())
        return help_text

    def _handle_status(self, command: dict, text: str) -> str:
        """Handle status command."""
        stats = self.state_manager.get_stats()
        return f"Mode: {stats['current_mode']}, Recordings: {stats['total_recordings']}"

    def _handle_settings(self, command: dict, text: str) -> str:
        """Handle settings command."""
        settings = self.state_manager.settings
        return f"Settings: {json.dumps(settings)}"

    def _handle_clear_cache(self, command: dict, text: str) -> str:
        """Handle clear cache command."""
        self.state_manager.clear_history()
        return "Cache cleared"

    def _handle_toggle_echo(self, command: dict, text: str) -> str:
        """Handle toggle echo command."""
        current = self.state_manager.get_setting('echo_detection', True)
        new_value = not current
        self.state_manager.set_setting('echo_detection', new_value)
        return f"Echo detection: {'enabled' if new_value else 'disabled'}"

    def _handle_toggle_auto_paste(self, command: dict, text: str) -> str:
        """Handle toggle auto-paste command."""
        current = self.state_manager.get_setting('auto_paste', True)
        new_value = not current
        self.state_manager.set_setting('auto_paste', new_value)
        return f"Auto-paste: {'enabled' if new_value else 'disabled'}"

    def _handle_set_language(self, command: dict, text: str) -> str:
        """Handle set language command."""
        # Extract language from text (e.g., "set language spanish" -> "spanish")
        parts = text.split()
        if len(parts) >= 3:
            language = parts[-1]
            self.state_manager.set_setting('language', language)
            return f"Language set to: {language}"
        return "Invalid language command"

    def _handle_set_mode(self, command: dict, text: str) -> str:
        """Handle set mode command."""
        mode_param = command.get('param')
        if mode_param == 'dictation':
            self.state_manager.set_mode(AssistantMode.DICTATION)
            return "Switched to dictation mode"
        elif mode_param == 'command':
            self.state_manager.set_mode(AssistantMode.COMMAND)
            return "Switched to command mode"
        elif mode_param == 'conversation':
            self.state_manager.set_mode(AssistantMode.CONVERSATION)
            return "Switched to conversation mode"
        return "Unknown mode"

    def _handle_show_history(self, command: dict, text: str) -> str:
        """Handle show history command."""
        history = self.state_manager.get_history(limit=10)
        return f"History: {json.dumps(history, indent=2)}"

    def _handle_undo_last(self, command: dict, text: str) -> str:
        """Handle undo last command."""
        return "Undo not yet implemented"

    def _handle_repeat_last(self, command: dict, text: str) -> str:
        """Handle repeat last command."""
        last = self.state_manager.get_last_transcription()
        if last:
            self.paster.paste_text(last)
            return f"Repeated: {last}"
        return "No previous transcription"

    def _handle_paste_text(self, command: dict, text: str) -> str:
        """Handle paste text command - pastes predefined text."""
        paste_text = command.get('text', '')
        if paste_text:
            self.paster.paste_text(paste_text, send_enter=True)
            return f"Pasted: {paste_text}"
        return "No text to paste"

    def _handle_reload_config(self, command: dict, text: str) -> str:
        """Handle reload config command - reloads configuration and commands."""
        try:
            # Reload configuration
            config_path = os.path.join(self.config_dir, "config.json")
            self.config_manager = ConfigManager(config_path)

            # Reload commands
            commands_path = os.path.join(self.config_dir, "commands.json")
            self.commands_manager = CommandsManager(commands_path)

            # Update command handler with new commands manager
            self.command_handler.commands_manager = self.commands_manager

            log("Configuration and commands reloaded successfully")
            return "Configuration reloaded successfully"
        except Exception as e:
            log(f"Failed to reload configuration: {e}")
            return f"Failed to reload configuration: {e}"

    def run(self):
        """Run the voice assistant in continuous mode."""
        try:
            while True:
                self.state_manager.set_state(AssistantState.IDLE)

                # Process audio and check if should continue
                if not self.process_audio_recording():
                    break

        except KeyboardInterrupt:
            log("Recording stopped by user", debug_only=True)

        except Exception as e:
            log(f"Error: {e}", debug_only=True)

        finally:
            self._shutdown()

    def _shutdown(self):
        """Cleanup on shutdown."""
        # Cleanup
        if self.recorder:
            self.recorder.stop()


def main():
    """Main entry point."""
    # Ensure only one instance runs at a time
    lock_file = Path(".cache/.voice_assistant.lock")
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Try to open lock file
        lock_fp = open(lock_file, 'w')
        fcntl.flock(lock_fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fp.write(f"{os.getpid()}")
        lock_fp.flush()
    except (IOError, OSError):
        print("Error: Voice Assistant is already running", file=sys.stderr)
        sys.exit(1)

    try:
        # Get config directory from argument or use default
        config_dir = sys.argv[1] if len(sys.argv) > 1 else "config"

        # Create and run assistant
        assistant = VoiceAssistant(config_dir=config_dir)
        assistant.run()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up lock file
        try:
            fcntl.flock(lock_fp.fileno(), fcntl.LOCK_UN)
            lock_fp.close()
            lock_file.unlink()
        except:
            pass


if __name__ == "__main__":
    main()
