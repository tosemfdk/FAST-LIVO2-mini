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


def _normalize_encoding_token(value: Any, fallback: str) -> str:
    text = str(value or fallback).strip()
    if not text:
        text = fallback
    return "_".join(text.split())


def _build_sequence_line(topic: str, message: Any, ts: float, config: RosbagConversionConfig) -> tuple[str, str]:
    if topic == config.imu_topic:
        return (
            "imu",
            "IMU {ts:.9f} {frame} {ax:.6f} {ay:.6f} {az:.6f} {gx:.6f} {gy:.6f} {gz:.6f}".format(
                ts=ts,
                frame=getattr(message.header, "frame_id", "imu") if hasattr(message, "header") else "imu",
                ax=float(message.linear_acceleration.x),
                ay=float(message.linear_acceleration.y),
                az=float(message.linear_acceleration.z),
                gx=float(message.angular_velocity.x),
                gy=float(message.angular_velocity.y),
                gz=float(message.angular_velocity.z),
            ),
        )
    if topic == config.image_topic:
        payload = getattr(message, "data", b"")
        return (
            "image",
            "IMAGE {ts:.9f} {frame} {encoding} {width} {height} {payload_bytes}".format(
                ts=ts,
                frame=getattr(message.header, "frame_id", "camera") if hasattr(message, "header") else "camera",
                encoding=_normalize_encoding_token(
                    getattr(message, "format", None) or getattr(message, "encoding", None),
                    config.image_transport,
                ),
                width=int(getattr(message, "width", 0) or 0),
                height=int(getattr(message, "height", 0) or 0),
                payload_bytes=len(payload),
            ),
        )
    if topic == config.lidar_topic:
        return (
            "lidar",
            "LIDAR {ts:.9f} {frame} {points}".format(
                ts=ts,
                frame=getattr(message.header, "frame_id", "lidar") if hasattr(message, "header") else "lidar",
                points=_detect_lidar_point_count(message),
            ),
        )
    raise ValueError(f"unexpected topic for conversion: {topic}")


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

    def append_message(topic: str, message: Any, ts: float) -> None:
        nonlocal imu_count, image_count, lidar_count, last_ts
        last_ts = max(last_ts, ts)
        kind, line = _build_sequence_line(topic, message, ts, config)
        if kind == "imu":
            imu_count += 1
        elif kind == "image":
            image_count += 1
        elif kind == "lidar":
            lidar_count += 1
        lines.append(line)

    try:
        import rosbag  # type: ignore[import-not-found]
    except ImportError:
        rosbag = None  # type: ignore[assignment]

    if rosbag is not None and config.bag_path.suffix == ".bag":
        with rosbag.Bag(str(config.bag_path), "r") as bag:  # type: ignore[attr-defined]
            for topic, message, timestamp in bag.read_messages(
                topics=[config.image_topic, config.imu_topic, config.lidar_topic]
            ):
                append_message(topic, message, float(timestamp.to_sec()))
    else:
        try:
            from rosbags.highlevel import AnyReader
            from rosbags.typesys import Stores, get_typestore
        except ImportError as exc:  # pragma: no cover - exercised manually when rosbags is absent
            raise RuntimeError(
                "Offline conversion requires either the ROS1 rosbag module (.bag) or the optional rosbags package (.db3 rosbag2)."
            ) from exc

        bag_root = config.bag_path.parent if config.bag_path.suffix == ".db3" else config.bag_path
        typestore = get_typestore(Stores.ROS2_JAZZY)
        pending_records: list[tuple[float, int, str]] = []
        with AnyReader([bag_root], default_typestore=typestore) as reader:
            base_timestamp_ns = reader.start_time
            connections = [
                connection
                for connection in reader.connections
                if connection.topic in {config.image_topic, config.imu_topic, config.lidar_topic}
            ]
            for index, (connection, timestamp, rawdata) in enumerate(reader.messages(connections=connections)):
                ts = (timestamp - base_timestamp_ns) / 1_000_000_000.0
                message = reader.deserialize(rawdata, connection.msgtype)
                kind, line = _build_sequence_line(connection.topic, message, ts, config)
                last_ts = max(last_ts, ts)
                if kind == "imu":
                    imu_count += 1
                elif kind == "image":
                    image_count += 1
                elif kind == "lidar":
                    lidar_count += 1
                pending_records.append((ts, index, line))
        pending_records.sort(key=lambda item: (item[0], item[1]))
        lines.extend(line for _, _, line in pending_records)

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
