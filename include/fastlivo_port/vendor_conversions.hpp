#pragma once

#include "fastlivo_port/messages.hpp"
#include "fastlivo_port/vendor_compat.hpp"

namespace fastlivo_port {

sensor_msgs::Imu::Ptr to_vendor_imu(const ImuFrame& frame);
sensor_msgs::Image::Ptr to_vendor_image(const ImageFrame& frame);
sensor_msgs::PointCloud2::Ptr to_vendor_pointcloud2(const LidarFrame& frame);
nav_msgs::Odometry to_vendor_odometry(const OdometryFrame& frame);

ImuFrame from_vendor_imu(const sensor_msgs::Imu::ConstPtr& msg);
ImageFrame from_vendor_image(const sensor_msgs::ImageConstPtr& msg);
LidarFrame from_vendor_pointcloud2(const sensor_msgs::PointCloud2::ConstPtr& msg);

}  // namespace fastlivo_port
