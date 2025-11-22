#!/usr/bin/env python3
"""
Benchmark script for larger models (small, medium) with progress logging.
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

# Test larger models
MODELS = ['small', 'medium']

# Limited settings for quicker results
CPU_THREADS = [2, 4, 8]
BEAM_SIZES = [1]  # Only test fastest beam size
COMPUTE_TYPES = ['int8', 'float32']
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
    """Benchmark a specific configuration."""
    try:
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

        # Load model with progress
        print(f"  [1/2] Loading model... ", end='', flush=True)
        load_start = time.time()
        model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
            cpu_threads=cpu_threads,
            num_workers=1
        )
        load_time = time.time() - load_start
        print(f"done ({load_time:.2f}s)")

        # Transcribe with progress
        print(f"  [2/2] Transcribing... ", end='', flush=True)
        transcribe_start = time.time()
        segments, info = model.transcribe(
            audio_file,
            language=language,
            beam_size=beam_size,
            vad_filter=vad_filter,
            word_timestamps=False
        )

        segments_list = list(segments)
        text = " ".join([segment.text for segment in segments_list]).strip()
        transcribe_time = time.time() - transcribe_start
        print(f"done ({transcribe_time:.2f}s)")

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
        print(f"ERROR: {e}")
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

def run_benchmark(audio_file: str) -> List[Dict]:
    """Run benchmark for larger models."""
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        return []

    results = []

    # Calculate total tests
    total_tests = len(MODELS) * len(COMPUTE_TYPES) * len(CPU_THREADS) * len(BEAM_SIZES) * len(VAD_OPTIONS)

    print("=" * 80)
    print("WHISPER BENCHMARK (Larger Models: small, medium)")
    print("=" * 80)
    print(f"Audio file: {audio_file}")
    print(f"Models to test: {', '.join(MODELS)}")
    print(f"Total configurations: {total_tests}")
    print(f"Estimated time: ~{total_tests * 5}s (assuming 5s per test)")
    print("=" * 80)
    print()

    current_test = 0
    start_time = time.time()

    for model in MODELS:
        print(f"\n{'=' * 80}")
        print(f"MODEL: {model.upper()}")
        print('=' * 80)

        for compute_type in COMPUTE_TYPES:
            for cpu_threads in CPU_THREADS:
                for beam_size in BEAM_SIZES:
                    for vad in VAD_OPTIONS:
                        current_test += 1
                        elapsed = time.time() - start_time
                        avg_per_test = elapsed / current_test if current_test > 0 else 5
                        remaining = (total_tests - current_test) * avg_per_test

                        config_desc = (
                            f"{model} | {compute_type} | "
                            f"threads:{cpu_threads} | beam:{beam_size} | vad:{vad}"
                        )

                        print(f"\n[{current_test}/{total_tests}] Testing: {config_desc}")
                        print(f"  Progress: {current_test/total_tests*100:.1f}% | "
                              f"Elapsed: {elapsed:.0f}s | "
                              f"ETA: ~{remaining:.0f}s")

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
                            speed_indicator = "🚀" if result['transcribe_time'] < 1.0 else "⚡" if result['transcribe_time'] < 2.0 else "🐌"
                            print(f"\n  {speed_indicator} Result: {result['transcribe_time']}s transcription")
                            print(f"  📝 Text: {result['text'][:70]}...")
                        else:
                            print(f"  ❌ Failed")

    return results

def analyze_results(results: List[Dict]) -> None:
    """Analyze and display results."""
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    successful = [r for r in results if r.get('success', False)]

    if not successful:
        print("❌ No successful transcriptions")
        return

    by_speed = sorted(successful, key=lambda x: x['transcribe_time'])
    sub_1s = [r for r in successful if r['transcribe_time'] < 1.0]

    print(f"\n📊 Successful tests: {len(successful)}/{len(results)}")
    print(f"🚀 Sub-1-second configs: {len(sub_1s)}")

    print("\n" + "-" * 80)
    print("TOP 10 FASTEST CONFIGURATIONS")
    print("-" * 80)

    for i, r in enumerate(by_speed[:10], 1):
        indicator = "🚀" if r['transcribe_time'] < 1.0 else "⚡"
        print(f"\n{i}. {indicator} {r['transcribe_time']}s - {r['model']}")
        print(f"   Config: {r['compute_type']} | threads:{r['cpu_threads']} | "
              f"beam:{r['beam_size']} | vad:{r['vad_filter']}")
        print(f"   Text: {r['text'][:60]}...")

    if sub_1s:
        best = sub_1s[0]
        print("\n" + "-" * 80)
        print("✅ BEST SUB-1-SECOND CONFIGURATION")
        print("-" * 80)
        print(f"Model: {best['model']}")
        print(f"Compute: {best['compute_type']}")
        print(f"Threads: {best['cpu_threads']}")
        print(f"Beam size: {best['beam_size']}")
        print(f"VAD: {best['vad_filter']}")
        print(f"Speed: {best['transcribe_time']}s")

        print("\nconfig.json update:")
        print(json.dumps({
            "model": best['model'],
            "compute_type": best['compute_type'],
            "cpu_threads": best['cpu_threads'],
            "beam_size": best['beam_size'],
            "vad_filter": best['vad_filter']
        }, indent=2))
    else:
        print("\n⚠️  No sub-1-second configurations found.")
        print(f"The fastest was {by_speed[0]['transcribe_time']}s")

def save_results(results: List[Dict]) -> None:
    """Save results to JSON."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"benchmark_medium_large_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved: {output_file}")

def main():
    """Main execution."""
    audio_file = "test_sample.wav"

    if not os.path.exists(audio_file):
        print("❌ Test audio not found! Run: python3 record_test_auto.py")
        return 1

    results = run_benchmark(audio_file)
    analyze_results(results)
    save_results(results)

    return 0

if __name__ == '__main__':
    sys.exit(main())
