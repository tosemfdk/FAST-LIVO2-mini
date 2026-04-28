from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .records import EndRecord, ImageRecord, ImuRecord, LidarRecord, Record, iter_records


@dataclass(slots=True)
class SynchronizedMeasure:
    lidar: LidarRecord
    image: ImageRecord | None
    imu_samples: list[ImuRecord] = field(default_factory=list)


@dataclass(slots=True)
class SynchronizationStats:
    measure_count: int = 0
    lidar_without_image: int = 0
    empty_imu_windows: int = 0
    trailing_imu_dropped: int = 0
    saw_end: bool = False


class SequenceSynchronizer:
    def __init__(self, max_image_gap_sec: float = 0.2) -> None:
        self.max_image_gap_sec = max_image_gap_sec
        self._latest_image: ImageRecord | None = None
        self._imu_window: list[ImuRecord] = []
        self.stats = SynchronizationStats()

    def push(self, record: Record) -> SynchronizedMeasure | None:
        if isinstance(record, ImuRecord):
            self._imu_window.append(record)
            return None
        if isinstance(record, ImageRecord):
            self._latest_image = record
            return None
        if isinstance(record, LidarRecord):
            measure = SynchronizedMeasure(
                lidar=record,
                image=self._select_image(record.timestamp),
                imu_samples=list(self._imu_window),
            )
            self.stats.measure_count += 1
            if measure.image is None:
                self.stats.lidar_without_image += 1
            if not measure.imu_samples:
                self.stats.empty_imu_windows += 1
            self._imu_window.clear()
            return measure
        if isinstance(record, EndRecord):
            self.stats.saw_end = True
            self.stats.trailing_imu_dropped += len(self._imu_window)
            self._imu_window.clear()
            return None
        return None

    def _select_image(self, lidar_timestamp: float) -> ImageRecord | None:
        if self._latest_image is None:
            return None
        if abs(self._latest_image.timestamp - lidar_timestamp) > self.max_image_gap_sec:
            return None
        return self._latest_image


def build_measures(records: Iterable[Record], max_image_gap_sec: float = 0.2) -> tuple[list[SynchronizedMeasure], SynchronizationStats]:
    synchronizer = SequenceSynchronizer(max_image_gap_sec=max_image_gap_sec)
    measures: list[SynchronizedMeasure] = []
    for record in records:
        measure = synchronizer.push(record)
        if measure is not None:
            measures.append(measure)
    return measures, synchronizer.stats


def build_measures_from_lines(lines: Iterable[str], max_image_gap_sec: float = 0.2) -> tuple[list[SynchronizedMeasure], SynchronizationStats]:
    return build_measures(iter_records(lines), max_image_gap_sec=max_image_gap_sec)
