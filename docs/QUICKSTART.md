# Quick Start Guide - Voice Assistant v2.0

## 5-Minute Setup

### 1. Install Dependencies (2 minutes)

```bash
cd johnny-voice-assistant
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed pyaudio-0.2.13 numpy-1.24.0 faster-whisper-0.10.0 ...
```

### 2. Grant Accessibility Permissions (1 minute)

The assistant needs permission to control your keyboard for pasting:

1. Go to **System Preferences → Security & Privacy → Accessibility**
2. Click the **+** button
3. Navigate to `/usr/bin/python3` or your Terminal app
4. Click **Add**
5. Make sure it's checked in the list

> Tip: You might need to allow Terminal or the IDE you're using instead of python3 directly.

### 3. Run the Assistant (< 1 minute)

```bash
python core/assistant.py
```

**You should see:**
```
============================================================
Voice Assistant Started - 2025-11-19 23:15:30
Mode: dictation
Press Ctrl+C to stop
============================================================
Starting audio recording (waiting for sound...)
```

## First Time Usage

### Start Speaking

1. **Wait for the message:** "Listening for audio..."
2. **Speak clearly:** "Hello, this is a test"
3. **The assistant will:**
   - Detect your speech
   - Print: "Sound detected! Recording..."
   - Listen until you pause
   - Print: "Silence detected, stopping recording..."
   - Transcribe your audio
   - **Automatically paste the text** into your active window

### That's It!

The text appears automatically in whatever app you have active (email, chat, document, etc.).

## Basic Commands

Try these voice commands:

**Pause recording:**
```
"pause"
```

**Resume recording:**
```
"resume"
```

**See available commands:**
```
"help"
```

**Switch to command mode:**
```
"command mode"
```

**Stop the assistant:**
```
"stop"
```

## Configuration (Optional)

To customize the assistant, edit `config/config.json`:

### Change language:
```json
{
  "transcription": {
    "language": "es"  // Spanish
  }
}
```

### Faster transcription (less accurate):
```json
{
  "transcription": {
    "model": "tiny"  // Already default, super fast
  }
}
```

### Disable auto-paste:
```json
{
  "features": {
    "auto_paste": false
  }
}
```

## Troubleshooting

### "No audio is being captured"
```bash
# Test microphone
python -c "import pyaudio; \
p = pyaudio.PyAudio(); \
print(p.get_default_input_device_info())"
```

### "Text isn't pasting"
1. Make sure app window is active
2. Check accessibility permissions (see step 2 above)
3. Some apps don't support keyboard automation (try a text editor)

### "Microphone stays muted"
```bash
osascript -e 'set volume input volume 100'
```

### "Transcription is slow"
- Model is already optimized ("tiny")
- Reduce audio length (speak more concisely)
- Close other applications

### "Getting strange transcriptions"
- Reduce background noise
- Increase `silence_threshold` in config
- Check audio input level in System Preferences

## Files Created After First Run

```
logs/
├── voice_assistant_20251119.log  # Today's log
└── ...

files/
├── Artur Recordings/             # Your audio files
│   ├── 20251119_230645_615.wav   # Audio recording
│   └── 20251119_230645_615.json  # Transcription data
└── analytics/                    # Performance metrics
```

## Common Workflows

### Workflow 1: Quick Note-Taking
1. Open Notes app
2. Run assistant: `python core/assistant.py`
3. Say: "Remember to buy milk"
4. Text pastes automatically ✓

### Workflow 2: Email Dictation
1. Open Gmail and start composing
2. Run assistant
3. Say: "Hi Sarah, I wanted to follow up on our meeting yesterday"
4. Text pastes into email body ✓

### Workflow 3: Code Comments
1. Open code editor
2. Run assistant in command mode
3. Say: "add comment" or other custom commands
4. Let the assistant help with your workflow ✓

## Tips & Tricks

### Reduce latency
- Speak clearly and a bit slower
- Pause briefly after each sentence (natural speech)
- Keep sentences short

### Improve accuracy
- Reduce background noise
- Face the microphone
- Speak at natural volume (not whisper)
- Use simple words

### Fix mistakes
- Say "pause" to stop
- Delete wrong text manually
- Say "resume" and continue

### See what's happening
Run with debug logging:
```bash
# Edit config.json:
{
  "app": {
    "debug": true  // Extra console output
  }
}
```

Then check the logs:
```bash
tail -f logs/voice_assistant_*.log
```

## Next Steps

1. **Explore voice commands:** Say "help"
2. **Try different modes:** "command mode", "dictation mode"
3. **Customize settings:** Edit `config/config.json`
4. **Add custom commands:** Edit `config/commands.json`
5. **Read full documentation:** See README.md and ARCHITECTURE.md

## Getting Help

### Check the logs
```bash
cat logs/voice_assistant_*.log | grep ERROR
```

### Read documentation
- **README.md** - Features, installation, usage
- **ARCHITECTURE.md** - Technical details, how it works
- **ENHANCED_VOICE_ASSISTANT_SUMMARY.md** - What's new

### Test components individually
```bash
# Test audio
python -c "from core import AudioRecorder; \
r = AudioRecorder({}); print('Audio OK')"

# Test transcription
python -c "from core import SpeechRecognizer; \
s = SpeechRecognizer({}); print('Whisper OK')"
```

## Keyboard Shortcuts (macOS)

These are built-in macOS shortcuts that might help:

- **Cmd+V** - Paste (automatic in voice assistant)
- **Cmd+Z** - Undo (if text pastes wrong)
- **Cmd+A** - Select all (to replace text)
- **Cmd+X** - Cut (to remove text)

## Performance Expectations

| Task | Time |
|------|------|
| Open assistant | 5 seconds (first run loads model) |
| Subsequent runs | < 1 second |
| Speak and pause | 2-5 seconds |
| Transcription | 0.8-1.2 seconds |
| Auto-paste | < 1 second |
| **Total time from speech to text on screen** | **2-10 seconds** |

## What's Next?

Once comfortable with basic usage:

1. **Master voice commands** - Use "help" command
2. **Try different modes** - Command mode for advanced users
3. **Customize settings** - Tune for your environment
4. **Add custom commands** - Make it work YOUR way
5. **Read the architecture** - Understand how it works

---

**That's it!** You now have a fully functional voice assistant.

Happy dictating! 🎤✨
