# Adam Voice Assistant v2.0

A production-ready, modular voice recognition and dictation system for macOS. Enables hands-free voice input with automatic transcription, text processing, and intelligent pasting into active applications.

## Features

### Core Functionality
- ✅ **Real-time audio recording** with automatic silence detection
- ✅ **AI-powered transcription** using OpenAI's Whisper (via Faster-Whisper)
- ✅ **Automatic text pasting** into active applications
- ✅ **Text-to-speech feedback** using macOS native voices
- ✅ **Text preprocessing** - corrections, capitalization, punctuation fixing
- ✅ **Echo detection** - avoids repeating system responses

### Advanced Features
- ✅ **Voice commands** - 14+ built-in commands (stop, pause, help, etc.)
- ✅ **Multiple operating modes**:
  - Dictation mode (auto-paste enabled)
  - Command mode (voice command execution)
  - Conversation mode (multi-turn interaction)
  - Paused mode (microphone muted)
- ✅ **State management** - tracks history, statistics, settings
- ✅ **Comprehensive logging** - structured logging with file rotation
- ✅ **Configuration system** - JSON-based, easily customizable
- ✅ **Modular architecture** - clean separation of concerns

### User Experience
- ✅ **Intelligent silence detection** - stops recording at natural pauses
- ✅ **Pre-recording buffer** - captures speech onset correctly
- ✅ **Microphone muting during speech** - prevents feedback loops
- ✅ **Command history** - track recent transcriptions
- ✅ **Settings persistence** - save user preferences

## System Architecture

```
voice_assistant.py (Main Application)
├─ ConfigManager (Load config files)
├─ StateManager (Track state, history, stats)
├─ StructuredLogger (Logging)
├─ CommandsManager (Command definitions)
└─ Core Components:
   ├─ AudioRecorder (Record with silence detection)
   │  └─ record_until_silence()
   │     └─ silence detection algorithm
   │        └─ pre-speech buffer
   │
   ├─ SpeechRecognizer (Transcribe audio)
   │  └─ Whisper model (tiny)
   │     └─ Language detection
   │        └─ Confidence scoring
   │
   ├─ TextPreprocessor (Process transcription)
   │  ├─ Echo detection
   │  ├─ Text corrections
   │  ├─ Capitalization fixing
   │  └─ Punctuation fixing
   │
   ├─ TextPaster (Paste to active app)
   │  └─ Clipboard management
   │     └─ Keyboard automation
   │
   ├─ Speaker (Text-to-speech)
   │  ├─ Microphone control
   │  └─ Voice synthesis
   │
   └─ CommandHandler (Execute commands)
      └─ Route to action handlers
```

## Data Flow

Complete cycle from speech to pasted text:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER SPEAKS                                              │
│    "Hello, what's the weather?"                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. AUDIO RECORDING (AudioRecorder)                          │
│    - Wait for sound to start (threshold detection)          │
│    - Record while speaking (with pre-buffer)                │
│    - Stop when silence detected (1 second quiet)            │
│    - Save to: 20251119_230645_615.wav (44.1 kHz, 16-bit)  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. SPEECH-TO-TEXT (SpeechRecognizer)                        │
│    - Load Whisper model (cached)                            │
│    - Transcribe audio file                                  │
│    - Output: "hello what's the weather"                     │
│    - Save to: 20251119_230645_615.json                      │
│    - Language: en (probability: 0.99)                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. TEXT PREPROCESSING (TextPreprocessor)         [NEW]      │
│    - Check: Is this an echo? (compare to last spoken)       │
│      └─ If yes: Skip processing and return                  │
│    - Apply text corrections (gonna → going to)              │
│    - Fix capitalization (first word capital)                │
│    - Fix punctuation (add period at end)                    │
│    - Output: "Hello what's the weather."                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. COMMAND OR DICTATION PROCESSING                          │
│                                                             │
│    Branch A: COMMAND MODE                                   │
│    ├─ Is this a recognized command?                         │
│    ├─ Execute command action                                │
│    └─ Speak response via TTS                                │
│                                                             │
│    Branch B: DICTATION MODE                                 │
│    ├─ Add to history                                        │
│    ├─ Process as dictation                                  │
│    └─ Continue to auto-paste                                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. AUTO-PASTE (TextPaster)                                  │
│    - Copy text to clipboard                                 │
│    - Simulate Cmd+V (paste)                                 │
│    - Simulate Enter key                                     │
│    - Text appears in active window                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. OPTIONAL: TEXT-TO-SPEECH RESPONSE (Speaker)              │
│    - Mute microphone input (prevent feedback)               │
│    - Speak response: "Checking the weather..."              │
│    - Unmute microphone                                      │
│    - Save spoken text for echo detection                    │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- macOS 10.12+
- Python 3.8+
- Working microphone
- Accessibility permissions (for keyboard automation)

### Setup

1. Clone or download the enhanced voice assistant:
```bash
cd adam-voice-assistant-enhanced
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Grant accessibility permissions (required for pyautogui):
   - System Preferences → Security & Privacy → Accessibility
   - Add Terminal/Python to allowed apps

4. Verify installation:
```bash
python voice_assistant.py --help
```

## Usage

### Basic Usage
```bash
# Start voice assistant in dictation mode
python voice_assistant.py

# Or specify custom config directory
python voice_assistant.py custom/config
```

### Configuration

Edit `config/config.json` to customize:
- Audio parameters (sample rate, silence threshold, etc.)
- Transcription model (tiny, base, small, medium)
- Text preprocessing rules
- Operating modes
- Keyboard/paste delays

### Voice Commands

The assistant recognizes these voice commands:

| Command | Aliases | Description |
|---------|---------|-------------|
| `stop` | quit, exit, close | Stop the assistant |
| `pause` | hold, wait | Pause recording |
| `resume` | continue, start | Resume recording |
| `help` | info, ? | Show available commands |
| `status` | state | Show current status |
| `settings` | config | Show current settings |
| `clear_cache` | clean, reset | Clear history |
| `toggle_echo` | echo | Toggle echo detection |
| `toggle_auto_paste` | paste | Toggle auto-paste |
| `dictation_mode` | dictate | Switch to dictation mode |
| `command_mode` | - | Switch to command mode |
| `history` | list | Show last 10 transcriptions |
| `repeat` | again | Repeat last transcription |

### Operating Modes

#### Dictation Mode (Default)
- Auto-paste enabled
- Voice input is automatically pasted
- Best for quick note-taking
- Activate: `dictation_mode`

#### Command Mode
- Voice input processed as commands
- Execute application-specific actions
- Activate: `command_mode`

#### Conversation Mode (Experimental)
- Multi-turn conversation tracking
- Maintains context
- Activate: `conversation_mode`

#### Paused Mode
- Microphone is muted
- No recording happening
- Activate: `pause`

## Configuration

### Audio Configuration

```json
{
  "audio": {
    "sample_rate": 44100,           // Hz
    "channels": 1,                  // Mono
    "format": "int16",              // 16-bit PCM
    "chunk_size": 1024,             // Samples per chunk
    "silence_threshold": 700,       // Amplitude level for silence
    "silence_duration": 1.0,        // Seconds of silence to stop
    "min_recording_time": 0.5,      // Minimum seconds to record
    "max_silence_timeout": 5.0,     // Max idle time before timeout
    "buffer_size": 43               // Pre-speech buffer chunks
  }
}
```

### Transcription Configuration

```json
{
  "transcription": {
    "model": "tiny",                // Model: tiny, base, small, medium
    "device": "cpu",                // cpu or cuda
    "compute_type": "float32",      // float32 or int8
    "cpu_threads": 4,               // Thread count
    "language": "en",               // Default language
    "beam_size": 1,                 // Beam search size (1 = fastest)
    "vad_filter": false             // Voice activity detection
  }
}
```

### Text Preprocessing

Add custom correction rules in code:
```python
preprocessor.add_correction_rule("gonna", "going to")
preprocessor.add_correction_rule("wanna", "want to")
```

## Performance

- **Recording latency:** <100ms
- **Transcription time:** 0.8-1.2 seconds (audio dependent)
- **End-to-end latency:** 1-2 seconds from silence to pasted text
- **Audio file size:** ~50KB per second of audio
- **Memory usage:** ~300-500MB (model loaded)

## File Organization

```
adam-voice-assistant-enhanced/
├── config/
│   ├── config.json          # Main configuration
│   └── commands.json        # Voice commands
├── core/
│   ├── audio_recorder.py    # Audio recording component
│   ├── speech_recognizer.py # Transcription component
│   ├── text_preprocessor.py # Text processing component
│   ├── text_paster.py       # Auto-paste component
│   ├── speaker.py           # Text-to-speech component
│   ├── state_manager.py     # State tracking
│   └── __init__.py
├── handlers/
│   ├── command_handler.py   # Command processing
│   └── __init__.py
├── utils/
│   ├── logger.py            # Structured logging
│   ├── config_manager.py    # Configuration loading
│   └── __init__.py
├── voice_assistant.py       # Main application
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── files/
    ├── Artur Recordings/    # Audio files (WAV)
    ├── analytics/           # Performance metrics
    └── .cache/              # Temporary files
```

## Logging

All operations are logged to:
- **Console:** INFO level and above
- **File:** `logs/voice_assistant_YYYYMMDD.log` (DEBUG level)

Logs include:
- Recording duration and file size
- Transcription time and language
- Text preprocessing operations
- Command execution results
- Error messages with stack traces

## Troubleshooting

### No audio is being captured
```bash
# Check microphone is working
python -c "import pyaudio; p = pyaudio.PyAudio(); print(p.get_default_input_device_info())"
```

### Transcription is slow
- Use smaller model: `"tiny"` (fastest, less accurate)
- Reduce audio length (speak more concisely)
- Enable GPU if available: `"device": "cuda"`

### Text isn't pasting
- Grant accessibility permissions to Terminal/Python
- Verify target application accepts keyboard input
- Check clipboard is not in use by another app

### Microphone stays muted
```bash
# Manually unmute
osascript -e 'set volume input volume 100'
```

### High latency between speech and paste
- Reduce `pre_speak_delay` in config
- Use faster transcrip model
- Close other applications

## Architecture Highlights

### Modular Design
Each component is independent and can be:
- Tested in isolation
- Replaced with alternatives
- Extended with custom logic
- Reused in other projects

### Error Recovery
- Graceful degradation if components fail
- Retry logic for transient errors
- Comprehensive error logging

### State Management
- Tracks assistant mode, state, and statistics
- Maintains transcription history
- Persists user preferences

### Configuration System
- Centralized JSON configuration
- Environment-specific overrides
- Validation of required settings
- Hot-reloading support

## Future Enhancements

Planned features for v2.1+:
- [ ] Real-time transcription while speaking
- [ ] Multi-language automatic detection
- [ ] Wake-word detection (don't require command prefix)
- [ ] Integration with online APIs (Weather, Calendar, etc.)
- [ ] Custom wake word training
- [ ] GPU acceleration support
- [ ] Web dashboard for monitoring
- [ ] Mobile app companion
- [ ] Cloud backup of transcriptions
- [ ] Integration with productivity apps (Slack, Teams, etc.)

## Contributing

To extend the assistant:

1. **Add custom commands:**
   - Edit `config/commands.json`
   - Implement handler in `voice_assistant.py`

2. **Customize text preprocessing:**
   - Add rules to `TextPreprocessor.correction_rules`
   - Or override `preprocess()` method

3. **Integrate new audio models:**
   - Modify `SpeechRecognizer` class
   - Update `config.json` parameters

4. **Add new operating modes:**
   - Create mode in `AssistantMode` enum
   - Implement in `_process_audio_recording()`

## Performance Tuning

### For faster transcription:
```json
{
  "transcription": {
    "model": "tiny",
    "compute_type": "float32",
    "cpu_threads": 8
  }
}
```

### For better accuracy:
```json
{
  "transcription": {
    "model": "base",
    "beam_size": 5
  }
}
```

### For better audio detection:
```json
{
  "audio": {
    "silence_threshold": 600,
    "silence_duration": 0.8
  }
}
```

## License

Proprietary - Adam Voice Assistant

## Support

For issues, questions, or suggestions:
1. Check the logs: `logs/voice_assistant_*.log`
2. Review configuration in `config/config.json`
3. Verify all dependencies are installed: `pip install -r requirements.txt`
4. Test individual components in isolation

---

**Version:** 2.0.0
**Last Updated:** 2025-11-19
**Architecture:** Modular, production-ready
**Status:** Stable
