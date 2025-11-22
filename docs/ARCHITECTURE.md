# Voice Assistant v2.0 - System Architecture

## Overview

The Voice Assistant is a modular, event-driven application designed to process voice input through a well-defined pipeline. Each component is independent, testable, and extensible.

## Core Design Principles

1. **Modularity** - Independent components with clear interfaces
2. **Separation of Concerns** - Each component has a single responsibility
3. **Configuration-Driven** - Behavior controlled by JSON configs
4. **State Management** - Centralized state tracking
5. **Error Resilience** - Graceful degradation and recovery
6. **Observability** - Comprehensive logging and metrics

## Component Architecture

### 1. Configuration System

```
ConfigManager (utils/config_manager.py)
├── Loads: config/config.json
├── Provides: Centralized settings access
├── Features:
│   ├── Dot notation access (e.g., "audio.sample_rate")
│   ├── Default values for missing keys
│   ├── Configuration validation
│   └── Hot-reload capability
│
└── CommandsManager (utils/config_manager.py)
    ├── Loads: config/commands.json
    ├── Provides: Command definitions and matching
    └── Features:
        ├── Fuzzy matching (Levenshtein distance)
        ├── Alias support
        └── Command metadata
```

**Key Methods:**
```python
config.get("audio.sample_rate", default=44100)
config.set("audio.sample_rate", 48000)
config.get_section("audio")  # Returns entire section
config.validate()  # Checks required fields

commands.get_command("stop")  # Get by name or alias
commands.list_commands()  # All available commands
```

### 2. State Management

```
StateManager (core/state_manager.py)
├── Tracks: Assistant mode and state
├── Modes:
│   ├── DICTATION (auto-paste enabled)
│   ├── COMMAND (execute voice commands)
│   ├── CONVERSATION (multi-turn)
│   └── PAUSED (idle)
│
├── States:
│   ├── IDLE (waiting for input)
│   ├── LISTENING (recording)
│   ├── PROCESSING (transcribing)
│   ├── SPEAKING (TTS output)
│   └── ERROR (error state)
│
├── Features:
│   ├── Settings management
│   ├── History tracking (max 100 entries)
│   ├── Statistics collection
│   └── Session metrics
│
└── Data Structures:
    ├── settings: Dict[str, Any]  # Current settings
    ├── history: List[Dict]        # Transcription history
    ├── stats: Dict[str, int]      # Performance statistics
    └── session_start: datetime    # Session timestamp
```

**Key Methods:**
```python
state.set_mode(AssistantMode.DICTATION)
state.set_state(AssistantState.LISTENING)
state.add_to_history(transcription, metadata)
state.get_stats()  # Returns aggregated statistics
state.increment_stat('total_recordings')
```

### 3. Logging System

```
StructuredLogger (utils/logger.py)
├── Outputs:
│   ├── Console (INFO+ level, formatted)
│   └── File (DEBUG+ level, rotated daily)
│
├── Features:
│   ├── Structured JSON events
│   ├── File rotation (10MB max, 5 backups)
│   ├── Stack trace capture
│   └── Contextual metadata
│
└── Log Levels:
    ├── DEBUG (detailed execution flow)
    ├── INFO (important milestones)
    ├── WARNING (recoverable issues)
    ├── ERROR (failures with context)
    └── CRITICAL (system-level failures)
```

**Key Methods:**
```python
logger.debug("Detailed message")
logger.info("Milestone reached")
logger.error("Operation failed", exc_info=True)
logger.log_event("audio_recording", "record", duration=1.5,
                 file_size=65000)  # Structured event logging
```

## Processing Pipeline

### Pipeline Architecture

The voice assistant processes audio through a well-defined pipeline:

```
USER INPUT
    │
    ▼
┌─────────────────────────────────────────┐
│ 1. AUDIO RECORDING                      │
│    (AudioRecorder)                      │
│                                         │
│  Input:  Microphone stream              │
│  Process: Silence detection             │
│           Pre-speech buffering          │
│  Output: WAV file (44.1 kHz, 16-bit)   │
│  Time:   ~1-5 seconds                   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ 2. SPEECH RECOGNITION                   │
│    (SpeechRecognizer)                   │
│                                         │
│  Input:  WAV file                       │
│  Model:  OpenAI Whisper (tiny/small)    │
│  Output: JSON with transcription        │
│  Time:   ~0.8-1.2 seconds               │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ 3. TEXT PREPROCESSING [NEW]             │
│    (TextPreprocessor)                   │
│                                         │
│  Input:  Raw transcription string       │
│  Steps:                                 │
│    1. Echo detection                    │
│    2. Text corrections                  │
│    3. Capitalization fixing             │
│    4. Punctuation normalization         │
│  Output: Processed text + metadata      │
│  Time:   ~10-50 ms                      │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ 4. COMMAND OR DICTATION PROCESSING      │
│    (CommandHandler / StateManager)      │
│                                         │
│  Branch A: Command Mode                 │
│  ├─ Is recognized command?              │
│  ├─ Execute action                      │
│  └─ Generate response                   │
│                                         │
│  Branch B: Dictation Mode               │
│  ├─ Add to history                      │
│  ├─ Check inline commands               │
│  └─ Process as text input               │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ 5. AUTO-PASTE TO APP                    │
│    (TextPaster)                         │
│                                         │
│  Input:  Processed text                 │
│  Steps:                                 │
│    1. Copy to clipboard                 │
│    2. Simulate Cmd+V (paste)            │
│    3. Simulate Enter (optional)         │
│  Output: Text in active window          │
│  Time:   ~100-300 ms                    │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ 6. TEXT-TO-SPEECH RESPONSE (Optional)   │
│    (Speaker)                            │
│                                         │
│  Input:  Response text                  │
│  Steps:                                 │
│    1. Mute microphone                   │
│    2. Synthesize speech                 │
│    3. Unmute microphone                 │
│    4. Save for echo detection           │
│  Output: Audio + echo cache             │
│  Time:   ~2-5 seconds                   │
└─────────────────────────────────────────┘
```

### Detailed Component Descriptions

#### 1. AudioRecorder (core/audio_recorder.py)

**Responsibility:** Capture microphone input with intelligent silence detection

**Key Features:**
- Real-time audio stream analysis
- Adaptive silence detection (threshold-based)
- Pre-speech buffer (captures speech onset)
- Configurable recording parameters

**Algorithm:**

```
Phase 1: Wait for Speech Start
├─ Read audio chunks
├─ Keep sliding buffer of last N chunks
├─ Check each chunk: amplitude > threshold?
├─ If YES: recording_started = True
├─ If NO and timeout: return failure
└─ Move to Phase 2

Phase 2: Record Until Silence
├─ Append audio to frames
├─ Check amplitude < threshold?
├─ If YES: increment silent_chunks
│  ├─ If silent_chunks >= required: STOP
│  ├─ If total_silence > max_timeout: STOP
├─ If NO: reset silent_chunks counter
└─ Return frames
```

**Configuration:**
```json
{
  "silence_threshold": 700,      // Min amplitude for speech
  "silence_duration": 1.0,       // Seconds of silence to stop
  "min_recording_time": 0.5,     // Don't stop before this
  "max_silence_timeout": 5.0,    // Max seconds of silence
  "buffer_size": 43              // Pre-speech chunks to keep
}
```

**Performance:**
- Memory: ~1-2 MB (depends on recording duration)
- CPU: Minimal (amplitude calculation only)
- Latency: <100 ms for silence detection

---

#### 2. SpeechRecognizer (core/speech_recognizer.py)

**Responsibility:** Convert audio to text using AI

**Key Features:**
- Lazy model loading (cached after first load)
- Language detection (automatic or specified)
- Confidence scoring
- Error handling and retries

**Model Options:**
| Model | Speed | Accuracy | Memory | Latency |
|-------|-------|----------|--------|---------|
| tiny  | Very fast | 70% | 39 MB | 0.8s |
| base  | Fast | 85% | 140 MB | 2.0s |
| small | Medium | 90% | 466 MB | 4.0s |
| medium | Slow | 95% | 1.5 GB | 10.0s |

**Configuration:**
```json
{
  "model": "tiny",
  "device": "cpu",
  "compute_type": "float32",
  "cpu_threads": 4,
  "language": "en",
  "beam_size": 1,
  "vad_filter": false,
  "timeout": 30
}
```

**Output Format:**
```json
{
  "filename": "20251119_230645_615.wav",
  "filepath": "/path/to/recording.wav",
  "recording_length_seconds": 2.34,
  "transcription_time_seconds": 0.82,
  "transcription": "hello world",
  "language": "en",
  "language_probability": 0.98
}
```

---

#### 3. TextPreprocessor (core/text_preprocessor.py) [NEW]

**Responsibility:** Clean and normalize transcribed text

**Key Features:**
- Echo detection (compares to last spoken text)
- Text correction rules (built-in and custom)
- Capitalization normalization
- Punctuation fixing
- Metadata tracking

**Processing Steps:**

```
Input: "hello whats the weather"
       │
       ▼
   Echo Check
   ├─ Load last_spoken.txt
   ├─ Normalize both texts
   ├─ Calculate similarity
   ├─ If similarity > 0.7: RETURN (echo)
   └─ CONTINUE
       │
       ▼
   Apply Corrections
   ├─ "gonna" → "going to"
   ├─ "wanna" → "want to"
   ├─ Custom user rules
   └─ Result: "hello what's the weather"
       │
       ▼
   Fix Capitalization
   ├─ Capitalize first letter
   ├─ Capitalize after ., !, ?
   └─ Result: "Hello what's the weather"
       │
       ▼
   Fix Punctuation
   ├─ Add period if missing
   ├─ Remove space before punctuation
   ├─ Add space after punctuation
   └─ Result: "Hello what's the weather."
       │
       ▼
   Output: "Hello what's the weather."
```

**Correction Rules:**
```python
default_rules = {
    'gonna': 'going to',
    'wanna': 'want to',
    'gotta': 'got to',
    'kinda': 'kind of',
    'sorta': 'sort of',
}
```

**Echo Detection:**
- Uses word intersection (Jaccard similarity)
- Threshold: 0.7 (70% word overlap)
- Prevents re-speaking system responses

---

#### 4. TextPaster (core/text_paster.py)

**Responsibility:** Automatically paste text into active application

**Key Features:**
- Clipboard management
- Keyboard event simulation
- Timing synchronization
- Error recovery

**Paste Sequence:**

```
1. Copy to clipboard
   └─ pyperclip.copy(text)

2. Wait (delay_before_paste)
   └─ time.sleep(0.2)

3. Paste keyboard shortcut
   ├─ Hold Command
   ├─ Press V
   └─ Release Command

4. Wait (delay_after_paste)
   └─ time.sleep(0.1)

5. Optional: Press Enter
   └─ pyautogui.press('enter')
```

**Configuration:**
```json
{
  "delay_before_paste": 0.2,      // Seconds
  "delay_after_paste": 0.1,       // Seconds
  "send_enter": true              // Auto-submit?
}
```

**Requirements:**
- macOS (uses Cmd+V for paste)
- Accessibility permissions granted
- Target app accepts keyboard input

---

#### 5. Speaker (core/speaker.py)

**Responsibility:** Provide voice feedback using TTS

**Key Features:**
- macOS native 'say' command integration
- Voice selection (Alex, Victoria, etc.)
- Microphone muting during speech
- Last-spoken caching for echo detection

**TTS Workflow:**

```
1. Pre-speak delay
   └─ Wait 3 seconds (ensure recording cycle complete)

2. Save spoken text
   └─ Write to last_spoken.txt (for echo detection)

3. Mute microphone
   └─ osascript set volume input volume 0

4. Synthesize speech
   └─ say command

5. Unmute microphone
   └─ osascript set volume input volume 100
```

**Configuration:**
```json
{
  "voice": "com.apple.speech.synthesis.voice.Alex",
  "rate": 200,
  "pre_speak_delay": 3,
  "mute_input_before_speak": true,
  "mute_level": 0,
  "unmute_level": 100
}
```

**Available Voices:**
- Alex (English, male)
- Victoria (English, female)
- Samantha (English, female)
- Plus localized voices for other languages

---

#### 6. CommandHandler (handlers/command_handler.py)

**Responsibility:** Recognize and execute voice commands

**Key Features:**
- Fuzzy command matching
- Action dispatching
- Response generation
- Error handling

**Command Matching:**

```
Input: "stup"
       │
       ▼
   Exact Match?
   ├─ "stup" in commands → NO
   └─ FUZZY MATCH
       │
       ▼
   Levenshtein Distance
   ├─ distance("stup", "stop") = 1
   ├─ distance("stup", "pause") = 4
   └─ Find minimum: "stop" (distance = 1)
       │
       ▼
   Execute Action
   ├─ Get handler for action
   ├─ Call handler function
   └─ Return response
```

**Available Commands:**

| Command | Aliases | Action |
|---------|---------|--------|
| stop | quit, exit | stop_assistant |
| pause | hold | pause_recording |
| resume | continue | resume_recording |
| help | info, ? | show_help |
| status | state | show_status |
| settings | config | show_settings |
| dictation_mode | dictate | set_mode(dictation) |
| command_mode | - | set_mode(command) |

---

## Data Flow Diagrams

### Complete Session Flow

```
┌──────────────────────────────────────────────────────────┐
│ SESSION START (core/assistant.py.run())                 │
└────────┬─────────────────────────────────────────────────┘
         │
         ▼
   ┌─────────────────┐
   │ Load Config     │ → config/config.json
   │ Load Commands   │ → config/commands.json
   │ Init Logger     │ → logs/voice_assistant_*.log
   │ Init Components │ → All 6 core components
   └────────┬────────┘
            │
            ▼ (Loop starts here)
     ┌──────────────────┐
     │ STATE: IDLE      │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ STATE: LISTENING │
     │ Record audio     │
     │ Save to file     │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ STATE: PROCESSING│
     │ Transcribe       │
     │ Preprocess       │
     │ Check echo?      │
     └────────┬─────────┘
              │
         ┌────┴────┐
         │          │
      ECHO       NO ECHO
       │            │
    SKIP        ┌───┴──────┐
               │            │
          COMMAND?      DICTATION
           │                │
         EXECUTE           PASTE
         SPEAK              │
                        HISTORY
                            │
     ┌──────────────────────┘
     │
     ▼
   CONTINUE? ──→ YES: Loop continues
   (Ctrl+C)  ──→ NO: Cleanup and exit
     │
     ▼
   SHUTDOWN
   ├─ Log final statistics
   ├─ Stop recorder
   ├─ Close files
   └─ Exit
```

## Extension Points

### Adding Custom Commands

1. **Define command in config/commands.json:**
```json
{
  "my_command": {
    "aliases": ["my_alias"],
    "description": "What it does",
    "action": "my_action"
  }
}
```

2. **Register handler in core/assistant.py:**
```python
self.command_handler.register_action(
    "my_action",
    self._handle_my_command
)
```

3. **Implement handler method:**
```python
def _handle_my_command(self, command: dict, text: str) -> str:
    # Do something
    return "Response text"
```

### Adding Text Correction Rules

```python
preprocessor.add_correction_rule("ur", "your")
preprocessor.add_correction_rule("lol", "laugh out loud")
```

### Changing Model

```json
{
  "transcription": {
    "model": "base"  // Changed from "tiny"
  }
}
```

## Performance Optimization

### For Speed:
- Use `model: "tiny"`
- Set `beam_size: 1`
- Increase `cpu_threads` (match CPU cores)
- Reduce `silence_duration` (stop sooner)

### For Accuracy:
- Use `model: "small"` or larger
- Set `beam_size: 5`
- Enable `vad_filter: true`
- Reduce `silence_threshold` (more sensitive)

### For Memory:
- Use `model: "tiny"`
- Limit `history_size` in StateManager
- Clear cache periodically

## Error Handling Strategy

```
Audio Recording Error
├─ Log error with context
├─ Return False to continue
└─ Inform user (optional TTS)

Transcription Error
├─ Retry up to max_retries
├─ If all retries fail:
│  ├─ Log error
│  ├─ Increment error stat
│  └─ Continue (skip this audio)
└─ Never crash application

Text Preprocessing Error
├─ Log warning
├─ Return original text
└─ Continue with caution

Paste Error
├─ Log error
├─ Try alternative methods
├─ Inform user via TTS
└─ Continue

Command Execution Error
├─ Log error
├─ Generate error response
├─ Speak error response
└─ Continue
```

## Thread Safety

Currently single-threaded with background processes:
- Audio recording: Main thread
- Transcription: Background process (Popen)
- Pasting: Main thread

For multi-threaded version, use:
- `threading.Lock()` for state access
- `queue.Queue()` for inter-thread communication
- `asyncio` for concurrent operations

## Testing Strategy

### Unit Tests
```python
# Test audio recorder silence detection
# Test speech recognizer output format
# Test text preprocessing rules
# Test command matching (fuzzy)
```

### Integration Tests
```python
# Test end-to-end pipeline
# Test with mock audio file
# Test with various transcriptions
```

### Performance Tests
```python
# Measure latency of each component
# Profile memory usage
# Benchmark transcription times
```

## Monitoring and Metrics

Tracked statistics:
- `total_recordings`: Audio files processed
- `total_transcriptions`: Successful transcriptions
- `successful_pastes`: Text successfully pasted
- `errors`: Total errors encountered
- `session_duration_seconds`: Total runtime

## Future Architecture Improvements

1. **Async/await support** for concurrent operations
2. **Plugin system** for custom components
3. **Event bus** for loose coupling
4. **Database** for persistent history
5. **API server** for remote control
6. **Web UI** for monitoring
7. **Mobile app** for control
8. **Cloud sync** for multi-device

---

**Document Version:** 2.0
**Last Updated:** 2025-11-19
**Status:** Complete and Accurate
