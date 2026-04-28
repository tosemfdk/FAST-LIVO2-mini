#pragma once

#include "fastlivo_port/messages.hpp"

#include <optional>
#include <utility>
#include <vector>

namespace fastlivo_port {

struct SynchronizedMeasure {
  LidarFrame lidar{};
  std::optional<ImageFrame> image{};
  std::vector<ImuFrame> imu_samples{};
};

struct SynchronizerStats {
  std::size_t measure_count{};
  std::size_t lidar_without_image{};
  std::size_t empty_imu_windows{};
  std::size_t trailing_imu_dropped{};
  bool saw_end_marker{false};
};

class SequenceSynchronizer {
 public:
  explicit SequenceSynchronizer(double max_image_gap_sec = 0.2);

  void push_imu(const ImuFrame& frame);
  void push_image(const ImageFrame& frame);
  SynchronizedMeasure push_lidar(const LidarFrame& frame);
  void mark_end();

  const SynchronizerStats& stats() const { return stats_; }

 private:
  std::optional<ImageFrame> select_image(double lidar_timestamp) const;

  double max_image_gap_sec_{0.2};
  std::optional<ImageFrame> latest_image_{};
  std::vector<ImuFrame> imu_window_{};
  SynchronizerStats stats_{};
};

}  // namespace fastlivo_port
