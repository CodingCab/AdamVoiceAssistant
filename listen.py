#!/usr/bin/env python3
import subprocess
import sys
import os

# Get the app directory (where this script is located)
app_dir = os.path.dirname(os.path.abspath(__file__))

# Path to assistant.py in core folder
assistant_path = os.path.join(app_dir, 'core', 'assistant.py')

# Run with 'config' as the default directory for configs
try:
    subprocess.run([sys.executable, assistant_path, 'config'] + sys.argv[1:], cwd=app_dir)
except KeyboardInterrupt:
    sys.exit(0)
