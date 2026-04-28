#pragma once

#include "fastlivo_port/portable_livo_core.hpp"
#include "fastlivo_port/vendor_compat.hpp"

#include <optional>
#include <vector>

namespace fastlivo_port {

class PortableLIVMapperAdapter {
 public:
  explicit PortableLIVMapperAdapter(PortableLivoConfig config = {});

  void standard_pcl_cbk(const sensor_msgs::PointCloud2::ConstPtr& msg);
  void imu_cbk(const sensor_msgs::Imu::ConstPtr& msg);
  void img_cbk(const sensor_msgs::ImageConstPtr& msg);
  std::optional<OdometryFrame> finish_sequence(double end_timestamp);

  PortableLivoSummary summary() const;
  const std::vector<OdometryFrame>& emitted_odometry() const;

 private:
  PortableLivoCore core_;
};

}  // namespace fastlivo_port
