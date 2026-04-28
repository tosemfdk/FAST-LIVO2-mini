from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.replay import verify_sequence


def main() -> int:
    parser = argparse.ArgumentParser(description="Run replay-first validation for the portable FAST-LIVO2 scaffold")
    parser.add_argument("--sequence", required=True, help="Path to a .seq replay file")
    parser.add_argument("--runner", help="Path to fastlivo_replay_runner")
    parser.add_argument("--odometry-out", help="Optional output CSV path")
    args = parser.parse_args()

    result = verify_sequence(args.sequence, runner=args.runner, odometry_out=args.odometry_out)
    print(result.stdout)
    print(f"odometry_output={result.odometry_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
