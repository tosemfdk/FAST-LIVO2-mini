from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
import sys

from .bag_topics import probe_bag_topics
from .conversion import RosbagConversionConfig, convert_rosbag_to_sequence
from .dimos_bridge import sequence_to_bridge_events
from .replay import verify_sequence
from .sequence import read_sequence
from .sync import build_measures_from_lines


@dataclass(slots=True)
class ReplayPipelineResult:
    replay_dir: Path
    sequence_path: Path
    manifest_path: Path
    measures_path: Path
    dimos_events_path: Path
    odometry_output_path: Path
    summary_path: Path


def run_replay_pipeline(
    bag_path: str | Path,
    replay_dir: str | Path,
    runner: str | Path,
    image_topic: str = "",
    imu_topic: str = "",
    lidar_topic: str = "",
    image_transport: str = "",
    max_image_gap_sec: float = 0.2,
) -> ReplayPipelineResult:
    bag_path = Path(bag_path)
    replay_dir = Path(replay_dir)
    replay_dir.mkdir(parents=True, exist_ok=True)

    if not image_topic or not imu_topic or not lidar_topic:
        selection = probe_bag_topics(bag_path)
        image_topic = image_topic or selection.image_topic
        imu_topic = imu_topic or selection.imu_topic
        lidar_topic = lidar_topic or selection.lidar_topic
        image_transport = image_transport or selection.image_transport

    sequence_path, manifest_path = convert_rosbag_to_sequence(
        RosbagConversionConfig(
            bag_path=bag_path,
            output_dir=replay_dir,
            image_topic=image_topic,
            imu_topic=imu_topic,
            lidar_topic=lidar_topic,
            image_transport=image_transport or "compressed",
        )
    )

    lines, stats = read_sequence(sequence_path)
    measures, sync_stats = build_measures_from_lines(lines, max_image_gap_sec=max_image_gap_sec)
    measures_path = replay_dir / "measures.json"
    measures_path.write_text(
        json.dumps(
            {
                "stats": {
                    "measure_count": sync_stats.measure_count,
                    "lidar_without_image": sync_stats.lidar_without_image,
                    "empty_imu_windows": sync_stats.empty_imu_windows,
                    "trailing_imu_dropped": sync_stats.trailing_imu_dropped,
                    "saw_end": sync_stats.saw_end,
                },
                "measures": [
                    {
                        "lidar_timestamp": measure.lidar.timestamp,
                        "image_timestamp": measure.image.timestamp if measure.image else None,
                        "imu_count": len(measure.imu_samples),
                        "lidar_points": measure.lidar.point_count,
                    }
                    for measure in measures
                ],
            },
            indent=2,
        )
        + "\n"
    )

    dimos_events_path = replay_dir / "dimos-events.json"
    dimos_events = [
        {
            "topic": event.topic,
            "msg_type": event.msg_type,
            "timestamp": event.timestamp,
        }
        for event in sequence_to_bridge_events(sequence_path)
    ]
    dimos_events_path.write_text(json.dumps(dimos_events, indent=2) + "\n")

    odometry_output_path = replay_dir / "odometry.csv"
    verification = verify_sequence(sequence_path, runner=runner, odometry_out=odometry_output_path)

    summary_path = replay_dir / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "bag_path": str(bag_path),
                "sequence_path": str(sequence_path),
                "manifest_path": str(manifest_path),
                "stats": {
                    "imu_count": stats.imu_count,
                    "image_count": stats.image_count,
                    "lidar_count": stats.lidar_count,
                    "saw_end": stats.saw_end,
                },
                "sync": {
                    "measure_count": sync_stats.measure_count,
                    "lidar_without_image": sync_stats.lidar_without_image,
                    "empty_imu_windows": sync_stats.empty_imu_windows,
                },
                "verification_stdout": verification.stdout,
                "odometry_output_path": str(verification.odometry_output),
            },
            indent=2,
        )
        + "\n"
    )

    return ReplayPipelineResult(
        replay_dir=replay_dir,
        sequence_path=sequence_path,
        manifest_path=manifest_path,
        measures_path=measures_path,
        dimos_events_path=dimos_events_path,
        odometry_output_path=odometry_output_path,
        summary_path=summary_path,
    )
