#include "fastlivo_port/portable_runtime.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>

namespace fastlivo_port {

PortableRuntime::PortableRuntime(RuntimeConfig config) : config_(config) {}

void PortableRuntime::validate_timestamp(double timestamp, const char* stream_name) {
  if (timestamp < 0.0) {
    std::ostringstream oss;
    oss << stream_name << " timestamp must be non-negative";
    throw SequenceError(oss.str());
  }
  if (config_.enforce_monotonic_timestamps && last_seen_timestamp_ > timestamp) {
    std::ostringstream oss;
    oss << "non-monotonic timestamp on " << stream_name << ": " << timestamp << " < "
        << last_seen_timestamp_;
    throw SequenceError(oss.str());
  }
  last_seen_timestamp_ = std::max(last_seen_timestamp_, timestamp);
  summary_.latest_timestamp = last_seen_timestamp_;
}

void PortableRuntime::push_imu(const ImuFrame& frame) {
  validate_timestamp(frame.timestamp, "imu");
  latest_imu_ = frame;
  ++summary_.imu_count;
}

void PortableRuntime::push_image(const ImageFrame& frame) {
  validate_timestamp(frame.timestamp, "image");
  latest_image_ = frame;
  ++summary_.image_count;
}

void PortableRuntime::push_lidar(const LidarFrame& frame) {
  validate_timestamp(frame.timestamp, "lidar");
  if (frame.point_count < config_.min_points_per_lidar_frame) {
    throw SequenceError("lidar frame has too few points");
  }
  latest_lidar_ = frame;
  ++summary_.lidar_count;
  (void)maybe_emit_odometry(frame.timestamp);
}

std::optional<OdometryFrame> PortableRuntime::maybe_emit_odometry(double timestamp) {
  if (config_.require_imu && !latest_imu_) {
    return std::nullopt;
  }
  if (config_.require_image && !latest_image_) {
    return std::nullopt;
  }
  if (config_.require_lidar && !latest_lidar_) {
    return std::nullopt;
  }
  if (timestamp <= last_odometry_timestamp_) {
    return std::nullopt;
  }

  OdometryFrame odom;
  odom.timestamp = timestamp;
  odom.x = static_cast<double>(summary_.lidar_count) * 0.1;
  odom.y = static_cast<double>(summary_.image_count) * 0.01;
  odom.z = static_cast<double>(summary_.imu_count) * 0.001;
  odometry_log_.push_back(odom);
  ++summary_.odometry_count;
  last_odometry_timestamp_ = timestamp;
  return odom;
}

std::optional<OdometryFrame> PortableRuntime::consume_end_of_sequence(double timestamp) {
  validate_timestamp(timestamp, "end");
  summary_.saw_end_marker = true;
  if ((config_.require_lidar && summary_.lidar_count == 0) ||
      (config_.require_imu && summary_.imu_count == 0) ||
      (config_.require_image && summary_.image_count == 0)) {
    throw SequenceError("sequence ended before all required streams were observed");
  }
  auto final_odom = maybe_emit_odometry(timestamp);
  summary_.consumed_full_sequence = true;
  return final_odom;
}

}  // namespace fastlivo_port
