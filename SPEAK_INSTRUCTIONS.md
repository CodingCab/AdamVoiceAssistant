# Speech Output Instructions for AI Agents

## Overview
When you need to communicate with the user through speech/voice, use the `speak.py` script instead of outputting text.

## Script Location
```
/Users/arturhanusek/Library/CloudStorage/GoogleDrive-artur@myshiptown.com/Shared drives/ShipTown/Journal/files/scripts/speak.py
```

## How to Use

### Basic Usage
To speak text to the user, simply call the script:

```python
Bash(
    command='python3 "/Users/arturhanusek/Library/CloudStorage/GoogleDrive-artur@myshiptown.com/Shared drives/ShipTown/Journal/files/scripts/speak.py" "Your message here"',
    description="Speak to user"
)
```

### Important Notes

1. **Script runs in background by default**: The script is designed to start speech and return immediately. The speech plays in the background while your workflow continues.

2. **No need for `run_in_background` parameter**: You can call it normally - it won't block your execution.

3. **Quote your message**: Always wrap the message in double quotes and escape any special characters.

4. **Microphone handling**: The script automatically mutes the microphone while speaking and unmutes it after speech completes.

## Examples

### Single message
```python
Bash(
    command='python3 "/Users/arturhanusek/Library/CloudStorage/GoogleDrive-artur@myshiptown.com/Shared drives/ShipTown/Journal/files/scripts/speak.py" "Task completed successfully"',
    description="Announce completion"
)
```

### Message with special characters
```python
Bash(
    command='python3 "/Users/arturhanusek/Library/CloudStorage/GoogleDrive-artur@myshiptown.com/Shared drives/ShipTown/Journal/files/scripts/speak.py" "I\'ve processed 5 files and found 3 errors."',
    description="Report status"
)
```

### Multiple messages in sequence
```python
# First message
Bash(
    command='python3 "/Users/arturhanusek/Library/CloudStorage/GoogleDrive-artur@myshiptown.com/Shared drives/ShipTown/Journal/files/scripts/speak.py" "Starting the build process"',
    description="Announce start"
)

# Continue with actual work immediately - script returns right away
# Do the build...

# Second message when done
Bash(
    command='python3 "/Users/arturhanusek/Library/CloudStorage/GoogleDrive-artur@myshiptown.com/Shared drives/ShipTown/Journal/files/scripts/speak.py" "Build completed"',
    description="Announce completion"
)
```

## When to Use Speech

Use speech output when:
- User has activated "voice mode" or "speech mode"
- You need to provide audio feedback while performing long tasks
- The user explicitly requests voice responses
- You're responding to voice input

## When NOT to Use Speech

Do not use speech when:
- User hasn't activated voice mode
- Providing detailed technical output (code, logs, etc.)
- User is reading on screen
- In normal text conversation mode

## Technical Details

- **Engine**: macOS `say` command
- **Blocking**: Non-blocking (runs in background)
- **Microphone**: Automatically muted during speech
- **Analytics**: Automatically logged
- **Echo Detection**: Last spoken text is saved for echo detection in voice assistant
