from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))
if str(ROOT / "src/thirdparty/dimos") not in sys.path:
    sys.path.insert(0, str(ROOT / "src/thirdparty/dimos"))

from fastlivo_port.pipeline import run_replay_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe -> convert -> inspect -> replay-run a FAST-LIVO2 rosbag")
    parser.add_argument("--bag", required=True)
    parser.add_argument("--replay-dir", required=True)
    parser.add_argument("--runner", default="build/fastlivo_replay_runner")
    parser.add_argument("--image-topic", default="")
    parser.add_argument("--imu-topic", default="")
    parser.add_argument("--lidar-topic", default="")
    parser.add_argument("--image-transport", default="")
    parser.add_argument("--max-image-gap-sec", type=float, default=0.2)
    args = parser.parse_args()

    result = run_replay_pipeline(
        bag_path=args.bag,
        replay_dir=args.replay_dir,
        runner=args.runner,
        image_topic=args.image_topic,
        imu_topic=args.imu_topic,
        lidar_topic=args.lidar_topic,
        image_transport=args.image_transport,
        max_image_gap_sec=args.max_image_gap_sec,
    )
    print(f"sequence={result.sequence_path}")
    print(f"manifest={result.manifest_path}")
    print(f"measures={result.measures_path}")
    print(f"dimos_events={result.dimos_events_path}")
    print(f"odometry={result.odometry_output_path}")
    print(f"summary={result.summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
