from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.records import EndRecord, ImageRecord, ImuRecord, LidarRecord, parse_record


class RecordParsingTests(unittest.TestCase):
    def test_parse_imu(self) -> None:
        record = parse_record("IMU 1.0 imu 0 0 9.8 0.1 0.2 0.3")
        self.assertIsInstance(record, ImuRecord)
        self.assertEqual(record.frame_id, "imu")

    def test_parse_image(self) -> None:
        record = parse_record("IMAGE 1.0 camera compressed 640 480 1024")
        self.assertIsInstance(record, ImageRecord)
        self.assertEqual(record.encoding, "compressed")

    def test_parse_lidar(self) -> None:
        record = parse_record("LIDAR 1.0 lidar 12")
        self.assertIsInstance(record, LidarRecord)
        self.assertEqual(record.point_count, 12)

    def test_parse_end(self) -> None:
        record = parse_record("END 1.5")
        self.assertIsInstance(record, EndRecord)


if __name__ == "__main__":
    unittest.main()
