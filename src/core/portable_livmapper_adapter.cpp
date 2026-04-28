#include "fastlivo_port/portable_livmapper_adapter.hpp"

#include "fastlivo_port/vendor_conversions.hpp"

namespace fastlivo_port {

PortableLIVMapperAdapter::PortableLIVMapperAdapter(PortableLivoConfig config) : core_(config) {}

void PortableLIVMapperAdapter::standard_pcl_cbk(const sensor_msgs::PointCloud2::ConstPtr& msg) {
  core_.push_lidar(from_vendor_pointcloud2(msg));
}

void PortableLIVMapperAdapter::imu_cbk(const sensor_msgs::Imu::ConstPtr& msg) {
  core_.push_imu(from_vendor_imu(msg));
}

void PortableLIVMapperAdapter::img_cbk(const sensor_msgs::ImageConstPtr& msg) {
  core_.push_image(from_vendor_image(msg));
}

std::optional<OdometryFrame> PortableLIVMapperAdapter::finish_sequence(double end_timestamp) {
  return core_.finish(end_timestamp);
}

PortableLivoSummary PortableLIVMapperAdapter::summary() const { return core_.summary(); }

const std::vector<OdometryFrame>& PortableLIVMapperAdapter::emitted_odometry() const {
  return core_.emitted_odometry();
}

}  // namespace fastlivo_port
