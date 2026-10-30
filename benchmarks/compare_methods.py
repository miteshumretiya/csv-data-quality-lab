"""Compare I/O-oriented CSV profiling methods using real elapsed wall time."""
from __future__ import annotations
import argparse
import csv
import statistics
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qualitylab.analyser import profile_csv


def _one(path):
    return profile_csv(path, preview_limit=0).row_count


def benchmark(files: list[str], repeats: int = 3, workers: int = 4) -> dict[str, dict[str, float]]:
    if repeats <= 0 or workers <= 0 or not files:
        raise ValueError("Provide at least one CSV, one repeat and one worker.")
    methods = {
        "Sequential": lambda: [_one(file) for file in files],
        "Thread pool": lambda: list(ThreadPoolExecutor(max_workers=workers).map(_one, files)),
        "Process pool": lambda: _in_processes(files, workers),
    }
    results = {}
    expected = None
    for label, method in methods.items():
        times = []
        for _ in range(repeats):
            start = time.perf_counter()
            outcome = method()
            seconds = time.perf_counter() - start
            if expected is None:
                expected = outcome
            if outcome != expected:
                raise RuntimeError("The methods did not agree on their results.")
            times.append(seconds)
        results[label] = {"median": statistics.median(times), "min": min(times), "max": max(times)}
    return results


def _in_processes(files, workers):
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(_one, files))


def generate_demo(folder: Path, files: int = 6, rows: int = 5000):
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for num in range(files):
        path = folder / f"generated_orders_{num+1}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["order", "region", "units", "cost", "comment"])
            for i in range(rows):
                writer.writerow([num*rows+i, ["North", "South", "East", "West"][i % 4],
                                 (i * 13) % 42, round(i*.037+num, 2), "" if i % 17 == 0 else "ok"])
        paths.append(str(path))
    return paths


def main():
    parser = argparse.ArgumentParser(description="CSV profiling performance comparison")
    parser.add_argument("paths", nargs="*", help="CSV dataset paths; leave empty with --demo")
    parser.add_argument("--demo", action="store_true", help="Generate local synthetic CSV files and benchmark them")
    parser.add_argument("--rows", type=int, default=5000)
    parser.add_argument("--files", type=int, default=6)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.demo:
        with tempfile.TemporaryDirectory(prefix="csvlab_demo_") as directory:
            _execute(generate_demo(Path(directory), args.files, args.rows), args)
    elif args.paths:
        _execute(args.paths, args)
    else:
        parser.error("Supply CSV paths or use --demo")


def _execute(paths, args):
    print(f"Datasets: {len(paths)} | Workers: {args.workers} | Repeats: {args.repeats}")
    results = benchmark(paths, repeats=args.repeats, workers=args.workers)
    print(f"{'Approach':<18} {'Median (s)':>12} {'Min (s)':>12} {'Max (s)':>12} {'Speed-up':>10}")
    base = results["Sequential"]["median"]
    for name, r in results.items():
        print(f"{name:<18} {r['median']:12.4f} {r['min']:12.4f} {r['max']:12.4f} {base/r['median']:10.2f}x")
    # Illustrative theoretical upper bound; separately label from actual measurements.
    parallel_fraction, cores = .8, args.workers
    theoretical = 1 / ((1-parallel_fraction) + parallel_fraction/cores)
    print(f"Amdahl illustration: P=0.80, N={cores}; theoretical max speed-up={theoretical:.2f}x")
    print("Note: thread/process overhead and CSV parsing characteristics affect actual timings.")


if __name__ == "__main__":
    main()
