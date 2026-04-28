#include "fastlivo_port/portable_livo_core.hpp"

namespace fastlivo_port {

PortableLivoCore::PortableLivoCore(PortableLivoConfig config)
    : config_(config), runtime_(config.runtime), synchronizer_(config.max_image_gap_sec) {}

void PortableLivoCore::push_imu(const ImuFrame& frame) { synchronizer_.push_imu(frame); }

void PortableLivoCore::push_image(const ImageFrame& frame) { synchronizer_.push_image(frame); }

void PortableLivoCore::feed_measure(const SynchronizedMeasure& measure) {
  for (const auto& imu : measure.imu_samples) {
    runtime_.push_imu(imu);
  }
  if (measure.image) {
    runtime_.push_image(*measure.image);
  }
  runtime_.push_lidar(measure.lidar);
}

void PortableLivoCore::push_lidar(const LidarFrame& frame) { feed_measure(synchronizer_.push_lidar(frame)); }

std::optional<OdometryFrame> PortableLivoCore::finish(double end_timestamp) {
  synchronizer_.mark_end();
  return runtime_.consume_end_of_sequence(end_timestamp);
}

PortableLivoSummary PortableLivoCore::summary() const {
  PortableLivoSummary result;
  result.runtime = runtime_.summary();
  result.sync = synchronizer_.stats();
  return result;
}

}  // namespace fastlivo_port
