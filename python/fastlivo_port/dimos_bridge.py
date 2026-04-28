from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .records import EndRecord, ImageRecord, ImuRecord, LidarRecord, Record, iter_records
from .sequence import read_sequence

LIDAR_TOPIC = "/fastlivo/lidar"
IMU_TOPIC = "/fastlivo/imu"
IMAGE_TOPIC = "/fastlivo/image/compressed"
ODOMETRY_TOPIC = "/fastlivo/odometry"


@dataclass(slots=True)
class BridgeEvent:
    topic: str
    msg_type: str
    payload: Any
    timestamp: float


@dataclass(slots=True)
class CompressedImageEnvelope:
    ts: float
    frame_id: str
    encoding: str
    width: int
    height: int
    payload_bytes: int


@dataclass(slots=True)
class LidarEnvelope:
    ts: float
    frame_id: str
    point_count: int


def _import_dimos() -> tuple[Any, Any, Any, Any, Any] | None:
    try:
        from dimos.msgs.geometry_msgs import Pose, Twist, Vector3
        from dimos.msgs.nav_msgs import Odometry
        from dimos.msgs.sensor_msgs import Imu
    except Exception:
        return None
    return Vector3, Pose, Twist, Odometry, Imu


def record_to_bridge_event(record: Record) -> BridgeEvent | None:
    if isinstance(record, ImuRecord):
        imported = _import_dimos()
        if imported is None:
            payload = asdict(record)
        else:
            Vector3, _, _, _, Imu = imported
            payload = Imu(
                ts=record.timestamp,
                frame_id=record.frame_id,
                linear_acceleration=Vector3(record.ax, record.ay, record.az),
                angular_velocity=Vector3(record.gx, record.gy, record.gz),
            )
        return BridgeEvent(
            topic=IMU_TOPIC,
            msg_type="sensor_msgs.Imu",
            payload=payload,
            timestamp=record.timestamp,
        )
    if isinstance(record, ImageRecord):
        return BridgeEvent(
            topic=IMAGE_TOPIC,
            msg_type="sensor_msgs.CompressedImageEnvelope",
            payload=CompressedImageEnvelope(
                ts=record.timestamp,
                frame_id=record.frame_id,
                encoding=record.encoding,
                width=record.width,
                height=record.height,
                payload_bytes=record.payload_bytes,
            ),
            timestamp=record.timestamp,
        )
    if isinstance(record, LidarRecord):
        return BridgeEvent(
            topic=LIDAR_TOPIC,
            msg_type="sensor_msgs.PointCloud2Envelope",
            payload=LidarEnvelope(ts=record.timestamp, frame_id=record.frame_id, point_count=record.point_count),
            timestamp=record.timestamp,
        )
    if isinstance(record, EndRecord):
        imported = _import_dimos()
        if imported is None:
            payload = {"ts": record.timestamp, "frame_id": "odom", "child_frame_id": "base_link"}
        else:
            Vector3, Pose, Twist, Odometry, _ = imported
            payload = Odometry(
                ts=record.timestamp,
                frame_id="odom",
                child_frame_id="base_link",
                pose=Pose(position=[0.0, 0.0, 0.0]),
                twist=Twist(linear=Vector3(0.0, 0.0, 0.0), angular=Vector3(0.0, 0.0, 0.0)),
            )
        return BridgeEvent(
            topic=ODOMETRY_TOPIC,
            msg_type="nav_msgs.Odometry",
            payload=payload,
            timestamp=record.timestamp,
        )
    return None


def sequence_to_bridge_events(sequence: str | Path) -> list[BridgeEvent]:
    lines, _ = read_sequence(sequence)
    events: list[BridgeEvent] = []
    for record in iter_records(lines):
        event = record_to_bridge_event(record)
        if event is not None:
            events.append(event)
    return events
