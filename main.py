"""Command-line entry point of the testbench.

Usage examples:

  # Run on the default synthetic click track (120 BPM, 12 s)
  python main.py

  # Custom synthetic BPM/duration (handy as a regression test)
  python main.py --bpm 140 --duration 20

  # Load your own audio file
  python main.py --file path/to/song.mp3

  # Run only specific algorithms
  python main.py --algorithms energy_cpp,librosa_reference

  # Different block size (as on Daisy Seed: 48 or 256)
  python main.py --block-size 256

  # Do not open a matplotlib window, only save the PNG
  python main.py --no-show --output results/run_001.png

  # Just list the registered algorithms
  python main.py --list
"""

from __future__ import annotations
import argparse
from pathlib import Path
import sys
from typing import Optional, Sequence

from src import registry
from src.audio_io import generate_click_track, load_audio, DEFAULT_SR
from src.benchmark import run_benchmark
from src.visualization import plot_comparison


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Testbench for comparing real-time music tempo (BPM) detection algorithms",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--file", type=str, default=None,
                    help="Path to an audio file. If omitted, a synthetic click track is used.")
    p.add_argument("--bpm", type=float, default=120.0,
                    help="BPM of the synthetic signal (when --file is not set)")
    p.add_argument("--duration", type=float, default=12.0,
                    help="Duration of the synthetic signal, s")
    p.add_argument("--noise", type=float, default=0.0,
                    help="White noise level in the synthetic signal (0..1)")
    p.add_argument("--sample-rate", type=int, default=DEFAULT_SR,
                    help="Target sample rate")
    p.add_argument("--block-size", type=int, default=1024,
                    help="Processing block size (emulates the Daisy Seed audio callback)")
    p.add_argument("--algorithms", type=str, default=None,
                    help="Comma-separated list of algorithm keys (empty = all available)")
    p.add_argument("--output", type=str, default="results/comparison.png",
                    help="Where to save the PNG report")
    p.add_argument("--no-show", action="store_true",
                    help="Do not open a matplotlib window")
    p.add_argument("--list", action="store_true",
                    help="List the registered algorithms and exit")
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    registry.register_default_algorithms()

    if args.list:
        print("Available algorithms:")
        for k in registry.list_algorithms():
            print(f"  - {k}")
        return 0

    # 1. Load / generate audio
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            return 1
        print(f"Loading audio: {path}")
        audio, sr = load_audio(str(path), target_sr=args.sample_rate)
        print(f"  duration: {len(audio) / sr:.1f} s, sample rate: {sr} Hz")
        expected_bpm = None
    else:
        print(f"Using a synthetic click track: {args.bpm:.1f} BPM, "
               f"{args.duration:.1f} s, noise={args.noise}")
        audio, sr = generate_click_track(
            bpm=args.bpm,
            duration_sec=args.duration,
            sample_rate=args.sample_rate,
            noise_level=args.noise,
        )
        expected_bpm = args.bpm

    # 2. Select algorithms
    available = registry.list_algorithms()
    if args.algorithms:
        keys = [k.strip() for k in args.algorithms.split(",") if k.strip()]
        unknown = [k for k in keys if k not in available]
        if unknown:
            print(f"Unknown algorithms: {unknown}", file=sys.stderr)
            print(f"Available: {available}", file=sys.stderr)
            return 1
    else:
        keys = available

    # 3. Run
    print(f"\nRunning benchmark ({len(keys)} algorithm(s), block_size={args.block_size}):")
    result = run_benchmark(audio, sr, keys, block_size=args.block_size)

    # 4. Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    if expected_bpm is not None:
        print(f"True BPM (synthetic): {expected_bpm:.2f}")
    if result.reference_bpm is not None:
        print(f"Reference BPM (librosa): {result.reference_bpm:.2f}")
    print()
    print(f"{'Algorithm':<28} {'BPM':>8} {'Error':>10} {'RT factor':>12}")
    print("-" * 62)
    errors = result.errors()
    for key, run in result.runs.items():
        err = errors.get(key)
        err_str = f"{err:+.2f}" if err is not None else "—"
        print(f"{run.algo_name:<28} {run.final_bpm:>8.2f} "
               f"{err_str:>10} {run.realtime_factor:>10.1f}x")
    print()

    # 5. Visualization
    plot_comparison(audio, sr, result,
                     output_path=Path(args.output),
                     show=not args.no_show)
    return 0


if __name__ == "__main__":
    sys.exit(main())
