from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.sequence import read_sequence
from fastlivo_port.records import iter_records, ImuRecord, ImageRecord, LidarRecord, EndRecord


class VendorShimFlowTests(unittest.TestCase):
    def test_smoke_sequence_record_types(self) -> None:
        lines, _ = read_sequence(ROOT / "tests/fixtures/smoke_sequence.seq")
        records = list(iter_records(lines))
        self.assertIsInstance(records[0], ImuRecord)
        self.assertIsInstance(records[1], ImageRecord)
        self.assertIsInstance(records[2], LidarRecord)
        self.assertIsInstance(records[-1], EndRecord)


if __name__ == "__main__":
    unittest.main()
