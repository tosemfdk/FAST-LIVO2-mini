from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.sequence import read_sequence, write_sequence


class SequenceTests(unittest.TestCase):
    def test_read_smoke_fixture(self) -> None:
        _, stats = read_sequence(ROOT / "tests/fixtures/smoke_sequence.seq")
        self.assertEqual(stats.imu_count, 2)
        self.assertEqual(stats.image_count, 2)
        self.assertEqual(stats.lidar_count, 2)
        self.assertTrue(stats.saw_end)

    def test_write_and_re_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "roundtrip.seq"
            stats = write_sequence(path, [
                "IMU 0.0 imu 0 0 9.8 0 0 0",
                "IMAGE 0.1 camera compressed 10 10 100",
                "LIDAR 0.2 lidar 3",
                "END 0.3",
            ])
            self.assertEqual(stats.imu_count, 1)
            self.assertEqual(stats.image_count, 1)
            self.assertEqual(stats.lidar_count, 1)
            self.assertTrue(stats.saw_end)


if __name__ == "__main__":
    unittest.main()
