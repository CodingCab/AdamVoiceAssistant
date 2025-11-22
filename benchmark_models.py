#!/usr/bin/env python3
"""
Comprehensive benchmark script to test different Whisper models and settings.
Tests transcription speed and accuracy across various configurations.
"""

import sys
import json
import time
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from faster_whisper import WhisperModel

# Test configurations to benchmark
MODELS = ['tiny', 'base', 'small', 'medium', 'large-v3']

# CPU threads to test (for CPU device)
CPU_THREADS = [1, 2, 4, 8]

# Beam sizes to test (affects accuracy vs speed)
BEAM_SIZES = [1, 5]

# Compute types to test
COMPUTE_TYPES = ['int8', 'float32']

# VAD filter options
VAD_OPTIONS = [True, False]

def benchmark_configuration(
    audio_file: str,
    model_name: str,
    device: str = 'cpu',
    compute_type: str = 'float32',
    cpu_threads: int = 4,
    beam_size: int = 1,
    vad_filter: bool = True,
    language: str = 'en'
) -> Dict:
    """
    Benchmark a specific configuration.

    Returns:
        Dict with benchmark results including transcription time, text, and config
    """
    try:
        # Fix OpenMP library conflict on macOS
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

        # Load model
        load_start = time.time()
        model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
            cpu_threads=cpu_threads,
            num_workers=1
        )
        load_time = time.time() - load_start

        # Transcribe
        transcribe_start = time.time()
        segments, info = model.transcribe(
            audio_file,
            language=language,
            beam_size=beam_size,
            vad_filter=vad_filter,
            word_timestamps=False  # Disable for faster processing
        )

        # Collect text
        segments_list = list(segments)
        text = " ".join([segment.text for segment in segments_list]).strip()
        transcribe_time = time.time() - transcribe_start

        return {
            'success': True,
            'model': model_name,
            'device': device,
            'compute_type': compute_type,
            'cpu_threads': cpu_threads,
            'beam_size': beam_size,
            'vad_filter': vad_filter,
            'load_time': round(load_time, 3),
            'transcribe_time': round(transcribe_time, 3),
            'total_time': round(load_time + transcribe_time, 3),
            'text': text,
            'text_length': len(text),
            'language': info.language,
            'language_probability': round(info.language_probability, 2)
        }

    except Exception as e:
        return {
            'success': False,
            'model': model_name,
            'device': device,
            'compute_type': compute_type,
            'cpu_threads': cpu_threads,
            'beam_size': beam_size,
            'vad_filter': vad_filter,
            'error': str(e)
        }

def run_comprehensive_benchmark(audio_file: str) -> List[Dict]:
    """
    Run comprehensive benchmarks across all model and setting combinations.

    Args:
        audio_file: Path to test audio file

    Returns:
        List of benchmark results
    """
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        return []

    results = []
    total_tests = 0

    # Calculate total number of tests
    for model in MODELS:
        for compute_type in COMPUTE_TYPES:
            for cpu_threads in CPU_THREADS:
                for beam_size in BEAM_SIZES:
                    for vad in VAD_OPTIONS:
                        total_tests += 1

    print("=" * 80)
    print("WHISPER MODEL BENCHMARK")
    print("=" * 80)
    print(f"Audio file: {audio_file}")
    print(f"Total configurations to test: {total_tests}")
    print("=" * 80)
    print()

    current_test = 0

    # Test all combinations
    for model in MODELS:
        print(f"\n{'=' * 80}")
        print(f"Testing model: {model}")
        print('=' * 80)

        for compute_type in COMPUTE_TYPES:
            # Skip int8 for tiny model as it might not be well optimized
            if model == 'tiny' and compute_type == 'int8':
                continue

            for cpu_threads in CPU_THREADS:
                for beam_size in BEAM_SIZES:
                    for vad in VAD_OPTIONS:
                        current_test += 1

                        config_desc = (
                            f"[{current_test}/{total_tests}] "
                            f"{model} | {compute_type} | "
                            f"threads:{cpu_threads} | beam:{beam_size} | vad:{vad}"
                        )

                        print(f"\nTesting: {config_desc}")

                        result = benchmark_configuration(
                            audio_file=audio_file,
                            model_name=model,
                            compute_type=compute_type,
                            cpu_threads=cpu_threads,
                            beam_size=beam_size,
                            vad_filter=vad
                        )

                        results.append(result)

                        if result['success']:
                            transcribe_time = result['transcribe_time']
                            speed_indicator = "🚀" if transcribe_time < 1.0 else "⚡" if transcribe_time < 2.0 else "🐌"
                            print(f"  {speed_indicator} Transcribe time: {transcribe_time}s")
                            print(f"  📝 Text preview: {result['text'][:80]}...")
                        else:
                            print(f"  ❌ Error: {result['error']}")

    return results

def analyze_results(results: List[Dict]) -> None:
    """
    Analyze benchmark results and provide recommendations.

    Args:
        results: List of benchmark results
    """
    print("\n" + "=" * 80)
    print("BENCHMARK ANALYSIS")
    print("=" * 80)

    # Filter successful results
    successful = [r for r in results if r.get('success', False)]

    if not successful:
        print("❌ No successful transcriptions")
        return

    # Sort by transcription time
    by_speed = sorted(successful, key=lambda x: x['transcribe_time'])

    # Find sub-1-second results
    sub_1s = [r for r in successful if r['transcribe_time'] < 1.0]

    print(f"\n📊 Total successful tests: {len(successful)}")
    print(f"🚀 Configurations under 1 second: {len(sub_1s)}")

    print("\n" + "-" * 80)
    print("TOP 10 FASTEST CONFIGURATIONS")
    print("-" * 80)

    for i, result in enumerate(by_speed[:10], 1):
        speed_indicator = "🚀" if result['transcribe_time'] < 1.0 else "⚡"
        print(f"\n{i}. {speed_indicator} {result['transcribe_time']}s - {result['model']}")
        print(f"   Compute: {result['compute_type']} | Threads: {result['cpu_threads']} | "
              f"Beam: {result['beam_size']} | VAD: {result['vad_filter']}")
        print(f"   Text: {result['text'][:60]}...")

    if sub_1s:
        print("\n" + "-" * 80)
        print("RECOMMENDED CONFIGURATION (fastest sub-1-second)")
        print("-" * 80)

        best = sub_1s[0]
        print(f"\n✅ Model: {best['model']}")
        print(f"✅ Compute type: {best['compute_type']}")
        print(f"✅ CPU threads: {best['cpu_threads']}")
        print(f"✅ Beam size: {best['beam_size']}")
        print(f"✅ VAD filter: {best['vad_filter']}")
        print(f"✅ Transcription time: {best['transcribe_time']}s")
        print(f"\n📝 Transcription: {best['text']}")

        print("\n" + "-" * 80)
        print("CONFIG.JSON UPDATE")
        print("-" * 80)
        print(json.dumps({
            "transcription": {
                "model": best['model'],
                "device": best['device'],
                "compute_type": best['compute_type'],
                "cpu_threads": best['cpu_threads'],
                "beam_size": best['beam_size'],
                "vad_filter": best['vad_filter']
            }
        }, indent=2))
    else:
        print("\n⚠️  No configurations achieved sub-1-second transcription.")
        print(f"The fastest was {by_speed[0]['transcribe_time']}s with model '{by_speed[0]['model']}'")

def save_results(results: List[Dict], output_file: str = None) -> None:
    """
    Save benchmark results to JSON file.

    Args:
        results: List of benchmark results
        output_file: Optional output file path
    """
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"benchmark_results_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")

def main():
    """Main benchmark execution."""
    audio_file = "test_sample.wav"

    if not os.path.exists(audio_file):
        print("❌ Test audio file not found!")
        print(f"Please run 'python3 record_test_sample.py' first to create {audio_file}")
        return 1

    # Run comprehensive benchmark
    results = run_comprehensive_benchmark(audio_file)

    # Analyze results
    analyze_results(results)

    # Save results
    save_results(results)

    return 0

if __name__ == '__main__':
    sys.exit(main())
