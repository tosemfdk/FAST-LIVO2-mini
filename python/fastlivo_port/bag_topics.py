from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class BagTopicSelection:
    image_topic: str
    imu_topic: str
    lidar_topic: str
    image_transport: str


_IMAGE_TYPES = {
    "sensor_msgs/CompressedImage": "compressed",
    "sensor_msgs/Image": "raw",
    "sensor_msgs/msg/CompressedImage": "compressed",
    "sensor_msgs/msg/Image": "raw",
}
_IMU_TYPES = {"sensor_msgs/Imu", "sensor_msgs/msg/Imu"}
_LIDAR_TYPES = {
    "sensor_msgs/PointCloud2",
    "livox_ros_driver/CustomMsg",
    "sensor_msgs/msg/PointCloud2",
}


def _normalize_rosbag2_path(bag_path: str | Path) -> Path:
    bag_path = Path(bag_path)
    if bag_path.is_dir():
        return bag_path
    if bag_path.suffix == ".db3" and (bag_path.parent / "metadata.yaml").exists():
        return bag_path.parent
    return bag_path


def _iter_topic_items(topic_info: Any):
    if isinstance(topic_info, dict):
        return topic_info.items()
    topics_attr = getattr(topic_info, "topics", None)
    if isinstance(topics_attr, dict):
        return topics_attr.items()
    raise TypeError("unsupported topic info container")


def select_topics_from_info(topic_info: Any) -> BagTopicSelection:
    image_topic = ""
    image_transport = "compressed"
    imu_topic = ""
    lidar_topic = ""

    for name, info in _iter_topic_items(topic_info):
        msg_type = getattr(info, "msg_type", None) or getattr(info, "datatype", None) or getattr(info, "type", None)
        if not image_topic and msg_type in _IMAGE_TYPES:
            image_topic = name
            image_transport = _IMAGE_TYPES[msg_type]
        if not imu_topic and msg_type in _IMU_TYPES:
            imu_topic = name
        if not lidar_topic and msg_type in _LIDAR_TYPES:
            lidar_topic = name

    if not image_topic or not imu_topic or not lidar_topic:
        raise RuntimeError(
            f"failed to auto-detect required topics (image={image_topic!r}, imu={imu_topic!r}, lidar={lidar_topic!r})"
        )

    return BagTopicSelection(
        image_topic=image_topic,
        imu_topic=imu_topic,
        lidar_topic=lidar_topic,
        image_transport=image_transport,
    )


def probe_bag_topics(bag_path: str | Path) -> BagTopicSelection:
    normalized_path = _normalize_rosbag2_path(bag_path)

    try:
        import rosbag  # type: ignore[import-not-found]
    except ImportError:
        rosbag = None  # type: ignore[assignment]

    if rosbag is not None and normalized_path.suffix == ".bag":
        with rosbag.Bag(str(normalized_path), "r") as bag:  # type: ignore[attr-defined]
            _, topic_info = bag.get_type_and_topic_info()
            return select_topics_from_info(topic_info)

    try:
        from rosbags.highlevel import AnyReader
        from rosbags.typesys import Stores, get_typestore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Topic probing requires either the ROS1 rosbag module (.bag) or the optional rosbags package (.db3 rosbag2)."
        ) from exc

    typestore = get_typestore(Stores.ROS2_JAZZY)
    with AnyReader([normalized_path], default_typestore=typestore) as reader:
        topic_info = {
            connection.topic: type(
                "Rosbag2TopicInfo",
                (),
                {
                    "msg_type": connection.msgtype,
                },
            )()
            for connection in reader.connections
        }
        return select_topics_from_info(topic_info)
