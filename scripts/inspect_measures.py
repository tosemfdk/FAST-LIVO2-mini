from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.sequence import read_sequence
from fastlivo_port.sync import build_measures_from_lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect synchronized lidar/image/imu measures from a replay sequence")
    parser.add_argument("--sequence", required=True)
    parser.add_argument("--max-image-gap-sec", type=float, default=0.2)
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    lines, _ = read_sequence(args.sequence)
    measures, stats = build_measures_from_lines(lines, max_image_gap_sec=args.max_image_gap_sec)
    payload = {
        "stats": {
            "measure_count": stats.measure_count,
            "lidar_without_image": stats.lidar_without_image,
            "empty_imu_windows": stats.empty_imu_windows,
            "trailing_imu_dropped": stats.trailing_imu_dropped,
            "saw_end": stats.saw_end,
        },
        "measures": [
            {
                "lidar_timestamp": measure.lidar.timestamp,
                "lidar_points": measure.lidar.point_count,
                "image_timestamp": measure.image.timestamp if measure.image else None,
                "imu_count": len(measure.imu_samples),
            }
            for measure in measures
        ],
    }
    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
