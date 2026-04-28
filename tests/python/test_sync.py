from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.sequence import read_sequence
from fastlivo_port.sync import build_measures_from_lines


class SyncTests(unittest.TestCase):
    def test_smoke_sequence_builds_two_measures(self) -> None:
        lines, _ = read_sequence(ROOT / "tests/fixtures/smoke_sequence.seq")
        measures, stats = build_measures_from_lines(lines)
        self.assertEqual(len(measures), 2)
        self.assertEqual(stats.measure_count, 2)
        self.assertEqual(stats.lidar_without_image, 0)
        self.assertEqual(stats.empty_imu_windows, 0)
        self.assertTrue(stats.saw_end)
        self.assertEqual(len(measures[0].imu_samples), 1)
        self.assertEqual(len(measures[1].imu_samples), 1)


if __name__ == "__main__":
    unittest.main()
