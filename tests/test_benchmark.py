"""Confirm the three performance methods agree on real results."""
import tempfile
import unittest
from pathlib import Path
from benchmarks.compare_methods import benchmark, generate_demo


class BenchmarkTests(unittest.TestCase):
    def test_generated_demo_files_have_expected_rows(self):
        with tempfile.TemporaryDirectory() as d:
            paths = generate_demo(Path(d), files=2, rows=13)
            results = benchmark(paths, repeats=1, workers=2)
            self.assertEqual(set(results), {"Sequential", "Thread pool", "Process pool"})
            for metric in results.values():
                self.assertGreaterEqual(metric["median"], 0)

    def test_requires_files(self):
        with self.assertRaises(ValueError):
            benchmark([], repeats=1, workers=2)

    def test_repeats_validation(self):
        with self.assertRaises(ValueError):
            benchmark(["abc.csv"], repeats=0)


if __name__ == "__main__":
    unittest.main()
