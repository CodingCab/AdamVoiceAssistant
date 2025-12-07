#!/bin/bash
# Usage: ./say.sh "text"
# Usage: VOICE=Zosia ./say.sh "text"  (for Polish)
# Usage: VOICE=Thomas ./say.sh "text" (for French)
# List voices: say -v '?'

VOICE_OPT=""
if [ -n "$VOICE" ]; then
    VOICE_OPT="-v $VOICE"
fi

nohup say -r 185 $VOICE_OPT "$*" >/dev/null 2>&1 &
disown
