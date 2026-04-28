from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

from .sequence import SequenceStats, read_sequence


@dataclass(slots=True)
class ReplayVerificationResult:
    stats: SequenceStats
    runner_used: str
    odometry_output: Path
    stdout: str


def verify_sequence(sequence: str | Path, runner: str | Path | None = None, odometry_out: str | Path | None = None) -> ReplayVerificationResult:
    sequence_path = Path(sequence)
    _, stats = read_sequence(sequence_path)
    if stats.imu_count == 0 or stats.image_count == 0 or stats.lidar_count == 0 or not stats.saw_end:
        raise RuntimeError("sequence is missing one or more required streams/end marker")

    runner_path = Path(runner) if runner else None
    if runner_path is None:
        discovered = shutil.which("fastlivo_replay_runner")
        runner_path = Path(discovered) if discovered else Path("build/fastlivo_replay_runner")
    if not runner_path.exists():
        raise RuntimeError(f"replay runner not found: {runner_path}")

    odom_path = Path(odometry_out) if odometry_out else sequence_path.with_suffix(".odometry.csv")
    completed = subprocess.run(
        [str(runner_path), "--sequence", str(sequence_path), "--odometry-out", str(odom_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return ReplayVerificationResult(stats=stats, runner_used=str(runner_path), odometry_output=odom_path, stdout=completed.stdout.strip())
