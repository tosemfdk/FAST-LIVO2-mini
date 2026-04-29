from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any

from .bag_topics import BagTopicSelection, probe_bag_topics


def _import_bridge_dependencies() -> dict[str, Any]:
    import lcm
    from dimos_lcm.sensor_msgs.CompressedImage import CompressedImage
    from dimos_lcm.sensor_msgs.Imu import Imu
    from dimos_lcm.sensor_msgs.PointCloud2 import PointCloud2
    from dimos_lcm.sensor_msgs.PointField import PointField
    from dimos_lcm.std_msgs.Header import Header
    from dimos_lcm.std_msgs.Time import Time
    from dimos_lcm.geometry_msgs.Point import Point
    from dimos_lcm.geometry_msgs.Pose import Pose
    from dimos_lcm.geometry_msgs.PoseWithCovariance import PoseWithCovariance
    from dimos_lcm.geometry_msgs.Quaternion import Quaternion
    from dimos_lcm.geometry_msgs.Twist import Twist
    from dimos_lcm.geometry_msgs.TwistWithCovariance import TwistWithCovariance
    from dimos_lcm.geometry_msgs.Vector3 import Vector3
    from dimos_lcm.nav_msgs.Odometry import Odometry
    from rosbags.highlevel import AnyReader
    from rosbags.typesys import Stores, get_typestore

    return {
        "lcm": lcm,
        "CompressedImage": CompressedImage,
        "Imu": Imu,
        "PointCloud2": PointCloud2,
        "PointField": PointField,
        "Header": Header,
        "Time": Time,
        "Point": Point,
        "Pose": Pose,
        "PoseWithCovariance": PoseWithCovariance,
        "Quaternion": Quaternion,
        "Twist": Twist,
        "TwistWithCovariance": TwistWithCovariance,
        "Vector3": Vector3,
        "Odometry": Odometry,
        "AnyReader": AnyReader,
        "Stores": Stores,
        "get_typestore": get_typestore,
    }


@dataclass(slots=True)
class DimosBridgeTopics:
    imu: str = "/fastlivo/imu"
    image: str = "/fastlivo/image/compressed"
    lidar: str = "/fastlivo/lidar"
    odometry: str = "/fastlivo/odometry"


@dataclass(slots=True)
class PublishedEvent:
    topic: str
    channel: str
    timestamp: float
    msg_name: str
    size_bytes: int


@dataclass(slots=True)
class PublishSummary:
    bag_path: Path
    imu_topic: str
    image_topic: str
    lidar_topic: str
    lcm_url: str
    replay_rate: float
    published_events: int
    published_topics: dict[str, int]
    first_timestamp: float | None
    last_timestamp: float | None


def lcm_channel_name(topic: str, msg_type: type[Any]) -> str:
    return f"{topic}#{msg_type.msg_name}"


def _normalize_rosbag2_path(bag_path: str | Path) -> Path:
    bag_path = Path(bag_path)
    if bag_path.is_dir():
        return bag_path
    if bag_path.suffix == ".db3" and (bag_path.parent / "metadata.yaml").exists():
        return bag_path.parent
    return bag_path


def _relative_seconds(timestamp_ns: int, base_timestamp_ns: int) -> float:
    return (timestamp_ns - base_timestamp_ns) / 1_000_000_000.0


def _header_time(stamp: Any | None, fallback_timestamp_ns: int, Time: type[Any]) -> Any:
    if stamp is not None and hasattr(stamp, "sec") and hasattr(stamp, "nanosec"):
        return Time(sec=int(stamp.sec), nsec=int(stamp.nanosec))
    sec = int(fallback_timestamp_ns // 1_000_000_000)
    nsec = int(fallback_timestamp_ns % 1_000_000_000)
    return Time(sec=sec, nsec=nsec)


def _make_header(message: Any, fallback_timestamp_ns: int, Header: type[Any], Time: type[Any]) -> Any:
    header = getattr(message, "header", None)
    frame_id = getattr(header, "frame_id", "") if header is not None else ""
    stamp = getattr(header, "stamp", None) if header is not None else None
    return Header(seq=0, stamp=_header_time(stamp, fallback_timestamp_ns, Time), frame_id=frame_id)


def _copy_vector3(source: Any, Vector3: type[Any]) -> Any:
    return Vector3(x=float(source.x), y=float(source.y), z=float(source.z))


def _copy_quaternion(source: Any, Quaternion: type[Any]) -> Any:
    return Quaternion(x=float(source.x), y=float(source.y), z=float(source.z), w=float(source.w))


def _copy_pose_default(Pose: type[Any], Point: type[Any], Quaternion: type[Any]) -> Any:
    return Pose(position=Point(x=0.0, y=0.0, z=0.0), orientation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0))


def _convert_imu(message: Any, timestamp_ns: int, deps: dict[str, Any]) -> Any:
    return deps["Imu"](
        header=_make_header(message, timestamp_ns, deps["Header"], deps["Time"]),
        orientation=_copy_quaternion(message.orientation, deps["Quaternion"]),
        orientation_covariance=list(message.orientation_covariance),
        angular_velocity=_copy_vector3(message.angular_velocity, deps["Vector3"]),
        angular_velocity_covariance=list(message.angular_velocity_covariance),
        linear_acceleration=_copy_vector3(message.linear_acceleration, deps["Vector3"]),
        linear_acceleration_covariance=list(message.linear_acceleration_covariance),
    )


def _convert_compressed_image(message: Any, timestamp_ns: int, deps: dict[str, Any]) -> Any:
    data = bytes(message.data)
    return deps["CompressedImage"](
        data_length=len(data),
        header=_make_header(message, timestamp_ns, deps["Header"], deps["Time"]),
        format=str(getattr(message, "format", "")),
        data=data,
    )


def _convert_point_field(field: Any, PointField: type[Any]) -> Any:
    return PointField(
        name=str(field.name),
        offset=int(field.offset),
        datatype=int(field.datatype),
        count=int(field.count),
    )


def _convert_point_cloud2(message: Any, timestamp_ns: int, deps: dict[str, Any]) -> Any:
    fields = [_convert_point_field(field, deps["PointField"]) for field in message.fields]
    data = bytes(message.data)
    return deps["PointCloud2"](
        fields_length=len(fields),
        data_length=len(data),
        header=_make_header(message, timestamp_ns, deps["Header"], deps["Time"]),
        height=int(message.height),
        width=int(message.width),
        fields=fields,
        is_bigendian=bool(message.is_bigendian),
        point_step=int(message.point_step),
        row_step=int(message.row_step),
        data=data,
        is_dense=bool(message.is_dense),
    )


def _convert_terminal_odometry(timestamp_ns: int, deps: dict[str, Any]) -> Any:
    return deps["Odometry"](
        header=deps["Header"](seq=0, stamp=_header_time(None, timestamp_ns, deps["Time"]), frame_id="odom"),
        child_frame_id="base_link",
        pose=deps["PoseWithCovariance"](pose=_copy_pose_default(deps["Pose"], deps["Point"], deps["Quaternion"])),
        twist=deps["TwistWithCovariance"](twist=deps["Twist"](
            linear=deps["Vector3"](x=0.0, y=0.0, z=0.0),
            angular=deps["Vector3"](x=0.0, y=0.0, z=0.0),
        )),
    )


def iter_rosbag2_dimos_messages(
    bag_path: str | Path,
    *,
    selection: BagTopicSelection | None = None,
    topics: DimosBridgeTopics | None = None,
    include_terminal_odometry: bool = True,
) -> Iterable[PublishedEvent]:
    deps = _import_bridge_dependencies()
    bag_root = _normalize_rosbag2_path(bag_path)
    selection = selection or probe_bag_topics(bag_root)
    topics = topics or DimosBridgeTopics()

    typestore = deps["get_typestore"](deps["Stores"].ROS2_JAZZY)
    with deps["AnyReader"]([bag_root], default_typestore=typestore) as reader:
        base_timestamp_ns = reader.start_time
        connections = [
            connection
            for connection in reader.connections
            if connection.topic in {selection.image_topic, selection.imu_topic, selection.lidar_topic}
        ]
        last_timestamp_ns = base_timestamp_ns
        for connection, timestamp_ns, rawdata in reader.messages(connections=connections):
            last_timestamp_ns = timestamp_ns
            message = reader.deserialize(rawdata, connection.msgtype)
            if connection.topic == selection.imu_topic:
                payload = _convert_imu(message, timestamp_ns, deps)
                topic = topics.imu
            elif connection.topic == selection.image_topic:
                payload = _convert_compressed_image(message, timestamp_ns, deps)
                topic = topics.image
            elif connection.topic == selection.lidar_topic:
                payload = _convert_point_cloud2(message, timestamp_ns, deps)
                topic = topics.lidar
            else:  # pragma: no cover
                continue

            yield PublishedEvent(
                topic=topic,
                channel=lcm_channel_name(topic, type(payload)),
                timestamp=_relative_seconds(timestamp_ns, base_timestamp_ns),
                msg_name=type(payload).msg_name,
                size_bytes=len(payload.lcm_encode()),
            ), payload

        if include_terminal_odometry:
            odom = _convert_terminal_odometry(last_timestamp_ns, deps)
            yield PublishedEvent(
                topic=topics.odometry,
                channel=lcm_channel_name(topics.odometry, type(odom)),
                timestamp=_relative_seconds(last_timestamp_ns, base_timestamp_ns),
                msg_name=type(odom).msg_name,
                size_bytes=len(odom.lcm_encode()),
            ), odom


def publish_rosbag2_to_dimos_lcm(
    bag_path: str | Path,
    *,
    selection: BagTopicSelection | None = None,
    topics: DimosBridgeTopics | None = None,
    lcm_url: str = "",
    replay_rate: float = 0.0,
    max_messages: int | None = None,
    include_terminal_odometry: bool = True,
) -> PublishSummary:
    deps = _import_bridge_dependencies()
    bag_path = Path(bag_path)
    normalized_path = _normalize_rosbag2_path(bag_path)
    selection = selection or probe_bag_topics(normalized_path)
    topics = topics or DimosBridgeTopics()

    lc = deps["lcm"].LCM(lcm_url) if lcm_url else deps["lcm"].LCM()
    return publish_dimos_events_to_lcm(
        lc,
        iter_rosbag2_dimos_messages(
            normalized_path,
            selection=selection,
            topics=topics,
            include_terminal_odometry=include_terminal_odometry,
        ),
        bag_path=normalized_path,
        selection=selection,
        lcm_url=lcm_url,
        replay_rate=replay_rate,
        max_messages=max_messages,
    )


def publish_dimos_events_to_lcm(
    lc: Any,
    events: Iterable[tuple[PublishedEvent, Any]],
    *,
    bag_path: Path,
    selection: BagTopicSelection,
    lcm_url: str = "",
    replay_rate: float = 0.0,
    max_messages: int | None = None,
) -> PublishSummary:
    published_topics: dict[str, int] = {}
    first_timestamp: float | None = None
    last_timestamp: float | None = None
    start_wall: float | None = None

    for index, (event, payload) in enumerate(events, start=1):
        if first_timestamp is None:
            first_timestamp = event.timestamp
            start_wall = time.monotonic()
        if replay_rate > 0.0 and start_wall is not None:
            target_elapsed = (event.timestamp - first_timestamp) / replay_rate
            sleep_for = target_elapsed - (time.monotonic() - start_wall)
            if sleep_for > 0:
                time.sleep(sleep_for)

        lc.publish(event.channel, payload.lcm_encode())
        published_topics[event.topic] = published_topics.get(event.topic, 0) + 1
        last_timestamp = event.timestamp

        if max_messages is not None and index >= max_messages:
            break

    return PublishSummary(
        bag_path=bag_path,
        imu_topic=selection.imu_topic,
        image_topic=selection.image_topic,
        lidar_topic=selection.lidar_topic,
        lcm_url=lcm_url or "default",
        replay_rate=replay_rate,
        published_events=sum(published_topics.values()),
        published_topics=published_topics,
        first_timestamp=first_timestamp,
        last_timestamp=last_timestamp,
    )
