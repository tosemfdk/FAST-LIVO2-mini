from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator


@dataclass(slots=True)
class ImuRecord:
    timestamp: float
    frame_id: str
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float


@dataclass(slots=True)
class ImageRecord:
    timestamp: float
    frame_id: str
    encoding: str
    width: int
    height: int
    payload_bytes: int


@dataclass(slots=True)
class LidarRecord:
    timestamp: float
    frame_id: str
    point_count: int


@dataclass(slots=True)
class EndRecord:
    timestamp: float


Record = ImuRecord | ImageRecord | LidarRecord | EndRecord


def parse_record(line: str) -> Record:
    tokens = line.split()
    if not tokens:
        raise ValueError("record line cannot be empty")
    kind = tokens[0]
    if kind == "IMU":
        if len(tokens) != 9:
            raise ValueError(f"invalid IMU record: {line}")
        return ImuRecord(
            timestamp=float(tokens[1]),
            frame_id=tokens[2],
            ax=float(tokens[3]),
            ay=float(tokens[4]),
            az=float(tokens[5]),
            gx=float(tokens[6]),
            gy=float(tokens[7]),
            gz=float(tokens[8]),
        )
    if kind == "IMAGE":
        if len(tokens) != 7:
            raise ValueError(f"invalid IMAGE record: {line}")
        return ImageRecord(
            timestamp=float(tokens[1]),
            frame_id=tokens[2],
            encoding=tokens[3],
            width=int(tokens[4]),
            height=int(tokens[5]),
            payload_bytes=int(tokens[6]),
        )
    if kind == "LIDAR":
        if len(tokens) != 4:
            raise ValueError(f"invalid LIDAR record: {line}")
        return LidarRecord(timestamp=float(tokens[1]), frame_id=tokens[2], point_count=int(tokens[3]))
    if kind == "END":
        if len(tokens) != 2:
            raise ValueError(f"invalid END record: {line}")
        return EndRecord(timestamp=float(tokens[1]))
    raise ValueError(f"unknown record kind: {kind}")


def iter_records(lines: Iterable[str]) -> Iterator[Record]:
    for line in lines:
        normalized = line.strip()
        if not normalized or normalized.startswith("#"):
            continue
        yield parse_record(normalized)
