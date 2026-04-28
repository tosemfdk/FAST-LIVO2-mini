#include "fastlivo_port/synchronizer.hpp"

#include <cmath>
#include <utility>

namespace fastlivo_port {

SequenceSynchronizer::SequenceSynchronizer(double max_image_gap_sec)
    : max_image_gap_sec_(max_image_gap_sec) {}

void SequenceSynchronizer::push_imu(const ImuFrame& frame) { imu_window_.push_back(frame); }

void SequenceSynchronizer::push_image(const ImageFrame& frame) { latest_image_ = frame; }

std::optional<ImageFrame> SequenceSynchronizer::select_image(double lidar_timestamp) const {
  if (!latest_image_) {
    return std::nullopt;
  }
  if (std::abs(latest_image_->timestamp - lidar_timestamp) > max_image_gap_sec_) {
    return std::nullopt;
  }
  return latest_image_;
}

SynchronizedMeasure SequenceSynchronizer::push_lidar(const LidarFrame& frame) {
  SynchronizedMeasure measure;
  measure.lidar = frame;
  measure.image = select_image(frame.timestamp);
  measure.imu_samples = std::move(imu_window_);
  imu_window_.clear();

  ++stats_.measure_count;
  if (!measure.image) {
    ++stats_.lidar_without_image;
  }
  if (measure.imu_samples.empty()) {
    ++stats_.empty_imu_windows;
  }
  return measure;
}

void SequenceSynchronizer::mark_end() {
  stats_.saw_end_marker = true;
  stats_.trailing_imu_dropped += imu_window_.size();
  imu_window_.clear();
}

}  // namespace fastlivo_port
