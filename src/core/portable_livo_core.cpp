#include "fastlivo_port/portable_livo_core.hpp"

#include <algorithm>
#include <vector>

namespace fastlivo_port {

PortableLivoCore::PortableLivoCore(PortableLivoConfig config)
    : config_(config), runtime_(config.runtime), synchronizer_(config.max_image_gap_sec) {}

void PortableLivoCore::push_imu(const ImuFrame& frame) { synchronizer_.push_imu(frame); }

void PortableLivoCore::push_image(const ImageFrame& frame) { synchronizer_.push_image(frame); }

void PortableLivoCore::feed_measure(const SynchronizedMeasure& measure) {
  struct TimedEvent {
    double timestamp;
    int order;
    const ImuFrame* imu;
    const ImageFrame* image;
    const LidarFrame* lidar;
  };

  std::vector<TimedEvent> events;
  events.reserve(measure.imu_samples.size() + (measure.image ? 1 : 0) + 1);
  for (const auto& imu : measure.imu_samples) {
    events.push_back(TimedEvent{imu.timestamp, 0, &imu, nullptr, nullptr});
  }
  if (measure.image) {
    events.push_back(TimedEvent{measure.image->timestamp, 1, nullptr, &*measure.image, nullptr});
  }
  events.push_back(TimedEvent{measure.lidar.timestamp, 2, nullptr, nullptr, &measure.lidar});

  std::sort(events.begin(), events.end(), [](const TimedEvent& lhs, const TimedEvent& rhs) {
    if (lhs.timestamp == rhs.timestamp) {
      return lhs.order < rhs.order;
    }
    return lhs.timestamp < rhs.timestamp;
  });

  for (const auto& event : events) {
    if (event.imu) {
      runtime_.push_imu(*event.imu);
    } else if (event.image) {
      runtime_.push_image(*event.image);
    } else if (event.lidar) {
      runtime_.push_lidar(*event.lidar);
    }
  }
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
