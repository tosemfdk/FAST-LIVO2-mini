from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.bag_topics import BagTopicSelection
from fastlivo_port.dimos_lcm_bridge import (
    _relative_seconds,
    PublishedEvent,
    lcm_channel_name,
    publish_dimos_events_to_lcm,
)


class DimosLcmBridgeTests(unittest.TestCase):
    def test_relative_seconds_uses_bag_start_offset(self) -> None:
        self.assertAlmostEqual(_relative_seconds(1_500_000_000, 1_000_000_000), 0.5)

    def test_channel_name_appends_msg_type(self) -> None:
        class Msg:
            msg_name = "sensor_msgs.Imu"

        self.assertEqual(lcm_channel_name("/fastlivo/imu", Msg), "/fastlivo/imu#sensor_msgs.Imu")

    def test_publish_dimos_events_to_lcm_counts_events(self) -> None:
        class FakeLCM:
            def __init__(self) -> None:
                self.published: list[tuple[str, bytes]] = []

            def publish(self, channel: str, payload: bytes) -> None:
                self.published.append((channel, payload))

        class FakeMsg:
            def __init__(self, data: bytes) -> None:
                self.data = data

            def lcm_encode(self) -> bytes:
                return self.data

        events = [
            (
                PublishedEvent("/fastlivo/imu", "/fastlivo/imu#sensor_msgs.Imu", 0.0, "sensor_msgs.Imu", 3),
                FakeMsg(b"imu"),
            ),
            (
                PublishedEvent(
                    "/fastlivo/image/compressed",
                    "/fastlivo/image/compressed#sensor_msgs.CompressedImage",
                    0.1,
                    "sensor_msgs.CompressedImage",
                    5,
                ),
                FakeMsg(b"image"),
            ),
        ]
        selection = BagTopicSelection(
            image_topic="/camera/image/compressed",
            imu_topic="/imu",
            lidar_topic="/lidar",
            image_transport="compressed",
        )
        fake_lc = FakeLCM()
        summary = publish_dimos_events_to_lcm(
            fake_lc,
            events,
            bag_path=Path("example.db3"),
            selection=selection,
            lcm_url="memq://",
            replay_rate=0.0,
        )
        self.assertEqual(summary.published_events, 2)
        self.assertEqual(summary.published_topics["/fastlivo/imu"], 1)
        self.assertEqual(summary.published_topics["/fastlivo/image/compressed"], 1)
        self.assertEqual(fake_lc.published[0], ("/fastlivo/imu#sensor_msgs.Imu", b"imu"))


if __name__ == "__main__":
    unittest.main()
