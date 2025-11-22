#!/usr/bin/env python3
import subprocess
import sys
import os
import json

# Get the app directory (where this script is located)
app_dir = os.path.dirname(os.path.abspath(__file__))

# Check for debug flag and enable debug mode
if '-d' in sys.argv or '--debug' in sys.argv:
    # Load config and temporarily enable debug mode
    config_path = os.path.join(app_dir, 'config', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    config['app']['debug'] = True
    config['app']['log_level'] = 'DEBUG'

    # Save temporarily
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    # Remove -d flag from args passed to assistant
    args = [arg for arg in sys.argv[1:] if arg not in ['-d', '--debug']]
else:
    args = sys.argv[1:]

# Path to assistant.py in core folder
assistant_path = os.path.join(app_dir, 'core', 'assistant.py')

# Run with 'config' as the default directory for configs
try:
    subprocess.run([sys.executable, assistant_path, 'config'] + args, cwd=app_dir)
except KeyboardInterrupt:
    sys.exit(0)
