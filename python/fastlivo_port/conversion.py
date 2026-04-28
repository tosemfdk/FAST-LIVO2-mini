from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .bag_topics import probe_bag_topics
from .sequence import SequenceManifest, write_manifest, write_sequence


@dataclass(slots=True)
class RosbagConversionConfig:
    bag_path: Path
    output_dir: Path
    image_topic: str
    imu_topic: str
    lidar_topic: str
    image_transport: str = "compressed"


def _detect_lidar_point_count(message: Any) -> int:
    if hasattr(message, "width") and hasattr(message, "height"):
        width = int(getattr(message, "width") or 0)
        height = int(getattr(message, "height") or 0)
        if width and height:
            return width * height
    if hasattr(message, "point_num"):
        return int(getattr(message, "point_num"))
    if hasattr(message, "points"):
        return len(getattr(message, "points"))
    if hasattr(message, "point_cloud"):
        return len(getattr(message, "point_cloud"))
    return 0


def convert_rosbag_to_sequence(config: RosbagConversionConfig) -> tuple[Path, Path]:
    if not config.image_topic or not config.imu_topic or not config.lidar_topic:
        selection = probe_bag_topics(config.bag_path)
        config = RosbagConversionConfig(
            bag_path=config.bag_path,
            output_dir=config.output_dir,
            image_topic=config.image_topic or selection.image_topic,
            imu_topic=config.imu_topic or selection.imu_topic,
            lidar_topic=config.lidar_topic or selection.lidar_topic,
            image_transport=config.image_transport or selection.image_transport,
        )
    try:
        import rosbag  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - exercised manually when ROS is absent
        raise RuntimeError(
            "rosbag Python module is required for offline conversion. Install the minimal ROS tooling only for this step."
        ) from exc

    config.output_dir.mkdir(parents=True, exist_ok=True)
    sequence_path = config.output_dir / "sequence.seq"
    manifest_path = config.output_dir / "manifest.json"

    lines: list[str] = [
        f"# source_bag {config.bag_path}",
        f"# image_topic {config.image_topic}",
        f"# imu_topic {config.imu_topic}",
        f"# lidar_topic {config.lidar_topic}",
    ]

    last_ts = 0.0
    imu_count = image_count = lidar_count = 0
    with rosbag.Bag(str(config.bag_path), "r") as bag:  # type: ignore[attr-defined]
        for topic, message, timestamp in bag.read_messages(topics=[config.image_topic, config.imu_topic, config.lidar_topic]):
            ts = float(timestamp.to_sec())
            last_ts = max(last_ts, ts)
            if topic == config.imu_topic:
                imu_count += 1
                lines.append(
                    "IMU {ts:.9f} {frame} {ax:.6f} {ay:.6f} {az:.6f} {gx:.6f} {gy:.6f} {gz:.6f}".format(
                        ts=ts,
                        frame=getattr(message.header, "frame_id", "imu") if hasattr(message, "header") else "imu",
                        ax=float(message.linear_acceleration.x),
                        ay=float(message.linear_acceleration.y),
                        az=float(message.linear_acceleration.z),
                        gx=float(message.angular_velocity.x),
                        gy=float(message.angular_velocity.y),
                        gz=float(message.angular_velocity.z),
                    )
                )
            elif topic == config.image_topic:
                image_count += 1
                payload = getattr(message, "data", b"")
                lines.append(
                    "IMAGE {ts:.9f} {frame} {encoding} {width} {height} {payload_bytes}".format(
                        ts=ts,
                        frame=getattr(message.header, "frame_id", "camera") if hasattr(message, "header") else "camera",
                        encoding=getattr(message, "format", None) or getattr(message, "encoding", None) or config.image_transport,
                        width=int(getattr(message, "width", 0) or 0),
                        height=int(getattr(message, "height", 0) or 0),
                        payload_bytes=len(payload),
                    )
                )
            elif topic == config.lidar_topic:
                lidar_count += 1
                lines.append(
                    "LIDAR {ts:.9f} {frame} {points}".format(
                        ts=ts,
                        frame=getattr(message.header, "frame_id", "lidar") if hasattr(message, "header") else "lidar",
                        points=_detect_lidar_point_count(message),
                    )
                )

    lines.append(f"END {last_ts:.9f}")
    stats = write_sequence(sequence_path, lines)
    manifest = SequenceManifest(
        source_bag=str(config.bag_path),
        image_topic=config.image_topic,
        imu_topic=config.imu_topic,
        lidar_topic=config.lidar_topic,
        image_transport=config.image_transport,
        stats={
            "imu_count": stats.imu_count,
            "image_count": stats.image_count,
            "lidar_count": stats.lidar_count,
            "saw_end": stats.saw_end,
        },
    )
    write_manifest(manifest_path, manifest)
    return sequence_path, manifest_path
