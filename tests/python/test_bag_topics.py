from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.bag_topics import select_topics_from_info


@dataclass
class TopicInfo:
    msg_type: str


class BagTopicTests(unittest.TestCase):
    def test_select_topics_prefers_compressed_image(self) -> None:
        selection = select_topics_from_info(
            {
                "/camera/image/compressed": TopicInfo("sensor_msgs/CompressedImage"),
                "/imu/data": TopicInfo("sensor_msgs/Imu"),
                "/livox/lidar": TopicInfo("livox_ros_driver/CustomMsg"),
            }
        )
        self.assertEqual(selection.image_topic, "/camera/image/compressed")
        self.assertEqual(selection.image_transport, "compressed")
        self.assertEqual(selection.imu_topic, "/imu/data")
        self.assertEqual(selection.lidar_topic, "/livox/lidar")

    def test_select_topics_accepts_ros2_type_names(self) -> None:
        selection = select_topics_from_info(
            {
                "/camera/camera/color/image_raw/compressed": TopicInfo("sensor_msgs/msg/CompressedImage"),
                "/livox/imu": TopicInfo("sensor_msgs/msg/Imu"),
                "/livox/lidar": TopicInfo("sensor_msgs/msg/PointCloud2"),
            }
        )
        self.assertEqual(selection.image_topic, "/camera/camera/color/image_raw/compressed")
        self.assertEqual(selection.image_transport, "compressed")
        self.assertEqual(selection.imu_topic, "/livox/imu")
        self.assertEqual(selection.lidar_topic, "/livox/lidar")


if __name__ == "__main__":
    unittest.main()
