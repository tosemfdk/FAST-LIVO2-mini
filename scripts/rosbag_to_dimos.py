from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.conversion import RosbagConversionConfig, convert_rosbag_to_sequence


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a ROS1 rosbag into the replay-first DimOS-ready sequence format used by this repo"
    )
    parser.add_argument("--bag", required=True, help="Path to rosbag file")
    parser.add_argument("--output-dir", required=True, help="Output directory for sequence and manifest")
    parser.add_argument("--image-topic")
    parser.add_argument("--imu-topic")
    parser.add_argument("--lidar-topic")
    parser.add_argument(
        "--image-transport",
        default="compressed",
        help="Image transport hint. Use 'compressed' for sensor_msgs/CompressedImage bags.",
    )
    args = parser.parse_args()

    sequence_path, manifest_path = convert_rosbag_to_sequence(
        RosbagConversionConfig(
            bag_path=Path(args.bag),
            output_dir=Path(args.output_dir),
            image_topic=args.image_topic,
            imu_topic=args.imu_topic,
            lidar_topic=args.lidar_topic,
            image_transport=args.image_transport,
        )
    )
    print(f"sequence={sequence_path}")
    print(f"manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
