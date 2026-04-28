#pragma once

#include "fastlivo_port/messages.hpp"

#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

namespace fastlivo_port {

struct RuntimeConfig {
  bool require_lidar{true};
  bool require_imu{true};
  bool require_image{true};
  bool enforce_monotonic_timestamps{true};
  std::size_t min_points_per_lidar_frame{1};
};

class SequenceError : public std::runtime_error {
 public:
  using std::runtime_error::runtime_error;
};

class PortableRuntime {
 public:
  explicit PortableRuntime(RuntimeConfig config = {});

  void push_imu(const ImuFrame& frame);
  void push_image(const ImageFrame& frame);
  void push_lidar(const LidarFrame& frame);
  std::optional<OdometryFrame> consume_end_of_sequence(double timestamp);

  const RuntimeSummary& summary() const { return summary_; }
  const std::vector<OdometryFrame>& emitted_odometry() const { return odometry_log_; }

 private:
  void validate_timestamp(double timestamp, const char* stream_name);
  std::optional<OdometryFrame> maybe_emit_odometry(double timestamp);

  RuntimeConfig config_;
  RuntimeSummary summary_;
  std::optional<ImuFrame> latest_imu_;
  std::optional<ImageFrame> latest_image_;
  std::optional<LidarFrame> latest_lidar_;
  std::vector<OdometryFrame> odometry_log_;
  double last_seen_timestamp_{-1.0};
  double last_odometry_timestamp_{-1.0};
};

}  // namespace fastlivo_port
