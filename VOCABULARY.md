# Whisper Vocabulary Customization

## Overview
You can improve transcription accuracy by providing Whisper with context about expected words and phrases.

## Configuration Location
Edit `config/config.json` in the `transcription` section.

## Available Options

### 1. Initial Prompt
Provides context to the model about expected vocabulary and style.

**Usage:**
```json
"initial_prompt": "Hey Johnny, Claude, task, project, code, bug, test, commit, push"
```

**Best Practices:**
- Include common technical terms you use
- Include proper nouns (names, product names)
- Include command words you frequently say
- Keep it under 224 tokens (~150-200 words)
- Use comma-separated words or short phrases

**Examples:**
```json
"initial_prompt": "GitHub, repository, pull request, merge, branch, Docker, Kubernetes, API, database"
```

### 2. Hotwords
Boosts specific words to be recognized more accurately (if supported by your Whisper version).

**Usage:**
```json
"hotwords": "Johnny:10 Claude:10 ShipTown:8"
```

Format: `word:boost_value` where boost_value is typically 1-10

**Note:** Hotwords support depends on the faster-whisper version. If not supported, it will be ignored.

## Tips for Better Transcription

1. **Add Technical Terms**: If you work with specific technologies, add them to initial_prompt
   ```json
   "initial_prompt": "React, TypeScript, Node.js, PostgreSQL, AWS, Lambda"
   ```

2. **Add Domain-Specific Words**: Include industry/domain terms
   ```json
   "initial_prompt": "e-commerce, inventory, warehouse, shipment, SKU, order fulfillment"
   ```

3. **Add Personal Names**: Include names you mention frequently
   ```json
   "initial_prompt": "Artur, Robert, Chris, Johnny, Claude"
   ```

4. **Add Wake Word**: Always include your wake word
   ```json
   "initial_prompt": "Hey Johnny"
   ```

5. **Combine Everything**: Create a comprehensive prompt
   ```json
   "initial_prompt": "Hey Johnny, Claude Code, GitHub, pull request, task, bug, test, commit, push, Docker, Kubernetes, ShipTown, warehouse, inventory, Artur, Robert, Chris"
   ```

## Current Configuration

Check `config/config.json` under the `transcription` section:
- `initial_prompt`: Context words/phrases for better recognition
- `hotwords`: Boosted words (if supported)

## Testing Changes

After updating the configuration:
1. Restart the voice assistant
2. Try speaking words that were previously misrecognized
3. Check if accuracy improves
4. Adjust the prompt based on results
