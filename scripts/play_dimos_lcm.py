from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.bag_topics import probe_bag_topics
from fastlivo_port.dimos_lcm_bridge import DimosBridgeTopics, publish_rosbag2_to_dimos_lcm


def main() -> int:
    parser = argparse.ArgumentParser(description="Play a ROS2 rosbag2 sqlite3 recording onto DimOS-style LCM channels.")
    parser.add_argument("--bag", required=True, help="Path to rosbag2 .db3 file or its directory")
    parser.add_argument("--imu-topic")
    parser.add_argument("--image-topic")
    parser.add_argument("--lidar-topic")
    parser.add_argument("--imu-channel", default="/fastlivo/imu")
    parser.add_argument("--image-channel", default="/fastlivo/image/compressed")
    parser.add_argument("--lidar-channel", default="/fastlivo/lidar")
    parser.add_argument("--odometry-channel", default="/fastlivo/odometry")
    parser.add_argument(
        "--lcm-url",
        default="",
        help="Optional LCM URL. Use memq:// for in-process smoke tests or a udpm://... URL where multicast routing works.",
    )
    parser.add_argument("--rate", type=float, default=0.0, help="Replay speed multiplier. 0 means publish as fast as possible.")
    parser.add_argument("--max-messages", type=int)
    parser.add_argument("--no-terminal-odometry", action="store_true")
    parser.add_argument("--summary-out", help="Optional JSON output path for publish summary")
    args = parser.parse_args()

    selection = probe_bag_topics(args.bag)
    if args.imu_topic:
        selection.imu_topic = args.imu_topic
    if args.image_topic:
        selection.image_topic = args.image_topic
    if args.lidar_topic:
        selection.lidar_topic = args.lidar_topic

    summary = publish_rosbag2_to_dimos_lcm(
        args.bag,
        selection=selection,
        topics=DimosBridgeTopics(
            imu=args.imu_channel,
            image=args.image_channel,
            lidar=args.lidar_channel,
            odometry=args.odometry_channel,
        ),
        lcm_url=args.lcm_url,
        replay_rate=args.rate,
        max_messages=args.max_messages,
        include_terminal_odometry=not args.no_terminal_odometry,
    )

    payload = {
        "bag_path": str(summary.bag_path),
        "imu_topic": summary.imu_topic,
        "image_topic": summary.image_topic,
        "lidar_topic": summary.lidar_topic,
        "lcm_url": summary.lcm_url,
        "replay_rate": summary.replay_rate,
        "published_events": summary.published_events,
        "published_topics": summary.published_topics,
        "first_timestamp": summary.first_timestamp,
        "last_timestamp": summary.last_timestamp,
    }
    if args.summary_out:
        Path(args.summary_out).write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
