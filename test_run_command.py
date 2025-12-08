#!/usr/bin/env python3
"""
Test for the run_command handler functionality.
"""

import subprocess
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))


def test_run_command_handler():
    """Test the run_command logic directly."""

    # Simulate the command config from commands.json
    command = {
        'name': 'claude_agent',
        'aliases': ['cloud', 'cloud agent', 'claude', 'claude agent', 'ask claude', 'hey claude'],
        'description': 'Run Claude agent with the spoken text as input',
        'action': 'run_command',
        'command': 'claude --agent .claude/agents/johnny-voice-assistant.md',
        'pass_speech': True,
        'fileName': ''
    }

    # Test cases: (input_text, expected_speech_extracted)
    test_cases = [
        ("cloud what is the weather", "what is the weather"),
        ("Cloud What is the weather", "What is the weather"),
        ("hey claude tell me a joke", "tell me a joke"),
        ("ask claude how are you", "how are you"),
        ("claude agent do something", "do something"),
    ]

    print("Testing speech extraction from trigger words:\n")

    for text, expected_speech in test_cases:
        # Replicate the logic from _handle_run_command
        cmd_name = command.get('name', '')
        aliases = command.get('aliases', [])

        speech = text
        text_lower = text.lower()

        triggers = sorted([cmd_name] + aliases, key=len, reverse=True)
        for trigger in triggers:
            trigger_lower = trigger.lower()
            if text_lower.startswith(trigger_lower):
                speech = text[len(trigger):].strip()
                break

        status = "✓" if speech == expected_speech else "✗"
        print(f"{status} Input: '{text}'")
        print(f"  Expected: '{expected_speech}'")
        print(f"  Got:      '{speech}'")
        print()


def test_command_execution():
    """Test actual command execution with a simple echo command."""

    print("\nTesting command execution:\n")

    # Test with a simple echo command
    command = {
        'name': 'test_echo',
        'aliases': ['echo'],
        'action': 'run_command',
        'command': 'echo',
        'pass_speech': True,
    }

    text = "echo hello world"

    # Extract speech
    cmd = command.get('command', '')
    cmd_name = command.get('name', '')
    aliases = command.get('aliases', [])

    speech = text
    text_lower = text.lower()

    triggers = [cmd_name] + aliases
    for trigger in triggers:
        trigger_lower = trigger.lower()
        if text_lower.startswith(trigger_lower):
            speech = text[len(trigger):].strip()
            break

    if speech:
        cmd = f'{cmd} "{speech}"'

    print(f"Command to execute: {cmd}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        print(f"Return code: {result.returncode}")
        print(f"Stdout: '{result.stdout.strip()}'")
        print(f"Stderr: '{result.stderr.strip()}'")

        if result.returncode == 0 and "hello world" in result.stdout:
            print("✓ Command execution test PASSED")
        else:
            print("✗ Command execution test FAILED")

    except Exception as e:
        print(f"✗ Exception: {e}")


def test_claude_command():
    """Test the actual claude command (if available)."""

    print("\nTesting claude command availability:\n")

    # First check if claude is available
    try:
        result = subprocess.run(
            "which claude",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            claude_path = result.stdout.strip()
            print(f"✓ Claude found at: {claude_path}")
        else:
            print("✗ Claude not found in PATH")
            return

    except Exception as e:
        print(f"✗ Error checking for claude: {e}")
        return

    # Test claude --help to verify it works
    print("\nTesting 'claude --help':")
    try:
        result = subprocess.run(
            "claude --help",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"First 200 chars of stdout: {result.stdout[:200]}...")
        if result.stderr:
            print(f"Stderr: {result.stderr[:200]}...")

    except Exception as e:
        print(f"✗ Error running claude --help: {e}")

    # Test the actual agent command structure
    print("\nTesting agent file existence:")
    agent_path = ".claude/agents/johnny-voice-assistant.md"
    full_path = os.path.join(os.path.dirname(__file__), "..", "..", agent_path)

    if os.path.exists(full_path):
        print(f"✓ Agent file exists: {full_path}")
    else:
        print(f"✗ Agent file NOT found: {full_path}")
        # Try from current working directory
        if os.path.exists(agent_path):
            print(f"✓ Agent file exists (relative): {agent_path}")
        else:
            print(f"✗ Agent file NOT found (relative): {agent_path}")


def test_full_claude_agent_command():
    """Test the full claude agent command as it would be executed."""

    print("\nTesting full claude agent command:\n")

    # Change to Journal directory where .claude folder exists
    journal_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    print(f"Working directory: {journal_dir}")

    command = {
        'name': 'claude_agent',
        'aliases': ['cloud', 'cloud agent', 'claude', 'claude agent', 'ask claude', 'hey claude'],
        'command': 'claude --agent .claude/agents/johnny-voice-assistant.md -p',
        'pass_speech': True,
    }

    text = "cloud say hello"

    # Extract speech (using fixed logic)
    cmd = command.get('command', '')
    cmd_name = command.get('name', '')
    aliases = command.get('aliases', [])

    speech = text
    text_lower = text.lower()

    triggers = sorted([cmd_name] + aliases, key=len, reverse=True)
    for trigger in triggers:
        trigger_lower = trigger.lower()
        if text_lower.startswith(trigger_lower):
            speech = text[len(trigger):].strip()
            break

    if speech:
        cmd = f'{cmd} "{speech}"'

    print(f"Input text: '{text}'")
    print(f"Extracted speech: '{speech}'")
    print(f"Full command: {cmd}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=journal_dir  # Run from Journal directory
        )

        print(f"\nReturn code: {result.returncode}")
        if result.stdout:
            print(f"Stdout:\n{result.stdout[:500]}")
        if result.stderr:
            print(f"Stderr:\n{result.stderr[:500]}")

        if result.returncode == 0:
            print("\n✓ Full claude agent command PASSED")
        else:
            print("\n✗ Full claude agent command FAILED")

    except subprocess.TimeoutExpired:
        print("✗ Command timed out (60s)")
    except Exception as e:
        print(f"✗ Exception: {e}")


def test_command_detection():
    """Test that CommandsManager detects prefix commands correctly."""
    from utils import CommandsManager

    print("\nTesting CommandsManager prefix detection:\n")

    # Load actual commands
    commands_file = os.path.join(os.path.dirname(__file__), "config", "commands.json")
    manager = CommandsManager(commands_file)

    test_cases = [
        ("Claude, say hello.", "claude_agent", True),
        ("cloud what is the weather", "claude_agent", True),
        ("hey claude tell me a joke", "claude_agent", True),
        ("stop", "stop", True),
        ("quit", "stop", True),  # alias
        ("random text here", None, False),
    ]

    for text, expected_cmd, should_match in test_cases:
        result = manager.get_command(text)

        if should_match:
            if result and result.get('name') == expected_cmd:
                print(f"✓ '{text}' -> {expected_cmd}")
            else:
                got = result.get('name') if result else None
                print(f"✗ '{text}' -> expected {expected_cmd}, got {got}")
        else:
            if result is None:
                print(f"✓ '{text}' -> None (as expected)")
            else:
                print(f"✗ '{text}' -> expected None, got {result.get('name')}")


if __name__ == "__main__":
    print("=" * 60)
    print("RUN_COMMAND Handler Tests")
    print("=" * 60)

    test_run_command_handler()
    test_command_execution()
    test_claude_command()
    test_command_detection()
    test_full_claude_agent_command()

    print("\n" + "=" * 60)
    print("Tests completed")
    print("=" * 60)
