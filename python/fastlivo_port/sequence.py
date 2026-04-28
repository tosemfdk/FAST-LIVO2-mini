from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class SequenceStats:
    imu_count: int = 0
    image_count: int = 0
    lidar_count: int = 0
    saw_end: bool = False


@dataclass(slots=True)
class SequenceManifest:
    source_bag: str = ""
    image_topic: str = ""
    imu_topic: str = ""
    lidar_topic: str = ""
    image_transport: str = "compressed"
    stats: dict[str, int | bool] = field(default_factory=dict)


def read_sequence(path: str | Path) -> tuple[list[str], SequenceStats]:
    sequence_path = Path(path)
    lines = [line.strip() for line in sequence_path.read_text().splitlines() if line.strip() and not line.startswith("#")]
    stats = SequenceStats()
    for line in lines:
        kind = line.split()[0]
        if kind == "IMU":
            stats.imu_count += 1
        elif kind == "IMAGE":
            stats.image_count += 1
        elif kind == "LIDAR":
            stats.lidar_count += 1
        elif kind == "END":
            stats.saw_end = True
    return lines, stats


def write_sequence(path: str | Path, lines: Iterable[str]) -> SequenceStats:
    normalized = [line.rstrip() for line in lines if line.strip()]
    Path(path).write_text("\n".join(normalized) + "\n")
    _, stats = read_sequence(path)
    return stats


def write_manifest(path: str | Path, manifest: SequenceManifest) -> None:
    Path(path).write_text(json.dumps({
        "source_bag": manifest.source_bag,
        "image_topic": manifest.image_topic,
        "imu_topic": manifest.imu_topic,
        "lidar_topic": manifest.lidar_topic,
        "image_transport": manifest.image_transport,
        "stats": manifest.stats,
    }, indent=2) + "\n")
