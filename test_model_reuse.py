#!/usr/bin/env python3
"""
Test to demonstrate the difference between loading model fresh vs reusing.
Shows real-world performance when model is loaded once and reused.
"""

import sys
import os
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from faster_whisper import WhisperModel

def test_fresh_load(audio_file: str, model_name: str, iterations: int = 5):
    """Test performance when loading model fresh each time (NOT realistic)."""
    print(f"\n{'=' * 80}")
    print(f"TEST 1: Loading model FRESH each time (benchmark approach)")
    print(f"Model: {model_name}")
    print('=' * 80)

    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

    total_load_time = 0
    total_transcribe_time = 0

    for i in range(iterations):
        print(f"\nIteration {i+1}/{iterations}")

        # Load model (fresh each time)
        print("  Loading model... ", end='', flush=True)
        load_start = time.time()
        model = WhisperModel(model_name, device='cpu', compute_type='float32', cpu_threads=8)
        load_time = time.time() - load_start
        total_load_time += load_time
        print(f"{load_time:.3f}s")

        # Transcribe
        print("  Transcribing... ", end='', flush=True)
        transcribe_start = time.time()
        segments, info = model.transcribe(audio_file, language='en', beam_size=1, vad_filter=True, word_timestamps=False)
        list(segments)  # Consume iterator
        transcribe_time = time.time() - transcribe_start
        total_transcribe_time += transcribe_time
        print(f"{transcribe_time:.3f}s")

    avg_load = total_load_time / iterations
    avg_transcribe = total_transcribe_time / iterations
    avg_total = avg_load + avg_transcribe

    print(f"\n{'─' * 80}")
    print("RESULTS:")
    print(f"  Average load time:       {avg_load:.3f}s")
    print(f"  Average transcribe time: {avg_transcribe:.3f}s")
    print(f"  Average TOTAL time:      {avg_total:.3f}s")
    print(f"  Total for {iterations} iterations: {total_load_time + total_transcribe_time:.3f}s")

def test_model_reuse(audio_file: str, model_name: str, iterations: int = 5):
    """Test performance when loading model ONCE and reusing (REALISTIC)."""
    print(f"\n{'=' * 80}")
    print(f"TEST 2: Loading model ONCE and reusing (real-world usage)")
    print(f"Model: {model_name}")
    print('=' * 80)

    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

    # Load model ONCE
    print(f"\n[STARTUP] Loading model... ", end='', flush=True)
    startup_start = time.time()
    model = WhisperModel(model_name, device='cpu', compute_type='float32', cpu_threads=8)
    startup_time = time.time() - startup_start
    print(f"{startup_time:.3f}s")
    print("\n✅ Model loaded! Ready for transcriptions.\n")

    # Now transcribe multiple times WITHOUT reloading
    total_transcribe_time = 0

    for i in range(iterations):
        print(f"Transcription {i+1}/{iterations}... ", end='', flush=True)
        transcribe_start = time.time()
        segments, info = model.transcribe(audio_file, language='en', beam_size=1, vad_filter=True, word_timestamps=False)
        list(segments)  # Consume iterator
        transcribe_time = time.time() - transcribe_start
        total_transcribe_time += transcribe_time
        print(f"{transcribe_time:.3f}s")

    avg_transcribe = total_transcribe_time / iterations

    print(f"\n{'─' * 80}")
    print("RESULTS:")
    print(f"  Startup (one-time):         {startup_time:.3f}s")
    print(f"  Average transcribe time:    {avg_transcribe:.3f}s")
    print(f"  Total for {iterations} iterations: {total_transcribe_time:.3f}s")
    print(f"\n  Time saved vs fresh loads: {(startup_time * (iterations-1)):.3f}s")

def compare_models(audio_file: str):
    """Compare different models with reuse."""
    models = ['tiny', 'base', 'small', 'medium']
    iterations = 10

    print(f"\n{'=' * 80}")
    print("MODEL COMPARISON (with model reuse)")
    print(f"Testing {iterations} transcriptions per model")
    print('=' * 80)

    results = []

    for model_name in models:
        print(f"\n{'─' * 80}")
        print(f"Model: {model_name.upper()}")
        print('─' * 80)

        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

        # Load once
        print(f"[STARTUP] Loading... ", end='', flush=True)
        load_start = time.time()
        model = WhisperModel(model_name, device='cpu', compute_type='float32', cpu_threads=8)
        load_time = time.time() - load_start
        print(f"{load_time:.3f}s")

        # Transcribe multiple times
        times = []
        for i in range(iterations):
            transcribe_start = time.time()
            segments, info = model.transcribe(audio_file, language='en', beam_size=1, vad_filter=True, word_timestamps=False)
            list(segments)
            transcribe_time = time.time() - transcribe_start
            times.append(transcribe_time)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        results.append({
            'model': model_name,
            'load_time': load_time,
            'avg_transcribe': avg_time,
            'min_transcribe': min_time,
            'max_transcribe': max_time
        })

        print(f"  Avg transcribe: {avg_time:.3f}s (min: {min_time:.3f}s, max: {max_time:.3f}s)")

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print('=' * 80)
    print(f"\n{'Model':<10} {'Startup':<12} {'Avg Trans':<12} {'Min Trans':<12} {'Max Trans':<12}")
    print('─' * 60)
    for r in results:
        print(f"{r['model']:<10} {r['load_time']:.3f}s{'':<6} {r['avg_transcribe']:.3f}s{'':<6} "
              f"{r['min_transcribe']:.3f}s{'':<6} {r['max_transcribe']:.3f}s")

    print("\n" + '=' * 80)
    print("KEY INSIGHT:")
    print("Startup time only happens ONCE when your app starts.")
    print("All subsequent transcriptions are just the 'Avg Trans' time!")
    print('=' * 80)

def main():
    audio_file = "test_sample.wav"

    if not os.path.exists(audio_file):
        print("❌ Test audio not found! Run: python3 record_test_auto.py")
        return 1

    print("\n" + "=" * 80)
    print("MODEL REUSE PERFORMANCE TEST")
    print("=" * 80)
    print(f"Audio file: {audio_file}")
    print("\nThis test demonstrates the difference between:")
    print("  1. Loading model fresh each time (benchmark approach)")
    print("  2. Loading once and reusing (real-world usage)")

    # Test with 'small' model as an example
    model = 'small'
    iterations = 5

    # Test 1: Fresh load each time
    test_fresh_load(audio_file, model, iterations)

    # Test 2: Load once and reuse
    test_model_reuse(audio_file, model, iterations)

    # Comparison across all models
    print("\n")
    compare_models(audio_file)

    return 0

if __name__ == '__main__':
    sys.exit(main())
