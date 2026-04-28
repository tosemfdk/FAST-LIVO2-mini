from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.bag_topics import probe_bag_topics


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe a rosbag and auto-detect image/imu/lidar topics")
    parser.add_argument("--bag", required=True)
    args = parser.parse_args()

    selection = probe_bag_topics(args.bag)
    print(json.dumps({
        "image_topic": selection.image_topic,
        "imu_topic": selection.imu_topic,
        "lidar_topic": selection.lidar_topic,
        "image_transport": selection.image_transport,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
