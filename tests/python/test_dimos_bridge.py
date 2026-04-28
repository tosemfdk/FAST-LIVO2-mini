from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))
if str(ROOT / "src/thirdparty/dimos") not in sys.path:
    sys.path.insert(0, str(ROOT / "src/thirdparty/dimos"))

try:
    from fastlivo_port.dimos_bridge import IMAGE_TOPIC, IMU_TOPIC, LIDAR_TOPIC, sequence_to_bridge_events
except Exception as exc:  # pragma: no cover
    sequence_to_bridge_events = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(sequence_to_bridge_events is None, f"DimOS bridge imports unavailable: {IMPORT_ERROR}")
class DimosBridgeTests(unittest.TestCase):
    def test_smoke_sequence_projects_topics(self) -> None:
        events = sequence_to_bridge_events(ROOT / "tests/fixtures/smoke_sequence.seq")
        topics = [event.topic for event in events]
        self.assertIn(IMU_TOPIC, topics)
        self.assertIn(IMAGE_TOPIC, topics)
        self.assertIn(LIDAR_TOPIC, topics)


if __name__ == "__main__":
    unittest.main()
