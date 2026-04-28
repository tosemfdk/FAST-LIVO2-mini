from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.sequence import read_sequence


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a converted replay sequence has all required streams")
    parser.add_argument("--sequence", required=True)
    args = parser.parse_args()

    _, stats = read_sequence(args.sequence)
    print(f"imu={stats.imu_count} image={stats.image_count} lidar={stats.lidar_count} saw_end={stats.saw_end}")
    if stats.imu_count == 0 or stats.image_count == 0 or stats.lidar_count == 0 or not stats.saw_end:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
