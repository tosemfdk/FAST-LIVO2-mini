#pragma once

#include "fastlivo_port/portable_runtime.hpp"
#include "fastlivo_port/synchronizer.hpp"

#include <optional>
#include <string>
#include <vector>

namespace fastlivo_port {

struct PortableLivoConfig {
  RuntimeConfig runtime{};
  double max_image_gap_sec{0.2};
};

struct PortableLivoSummary {
  RuntimeSummary runtime{};
  SynchronizerStats sync{};
};

class PortableLivoCore {
 public:
  explicit PortableLivoCore(PortableLivoConfig config = {});

  void push_imu(const ImuFrame& frame);
  void push_image(const ImageFrame& frame);
  void push_lidar(const LidarFrame& frame);
  std::optional<OdometryFrame> finish(double end_timestamp);

  const std::vector<OdometryFrame>& emitted_odometry() const { return runtime_.emitted_odometry(); }
  PortableLivoSummary summary() const;

 private:
  void feed_measure(const SynchronizedMeasure& measure);

  PortableLivoConfig config_{};
  PortableRuntime runtime_;
  SequenceSynchronizer synchronizer_;
};

}  // namespace fastlivo_port
