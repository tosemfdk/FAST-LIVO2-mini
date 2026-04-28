#include "fastlivo_port/vendor_conversions.hpp"

namespace fastlivo_port {

sensor_msgs::Imu::Ptr to_vendor_imu(const ImuFrame& frame) {
  auto msg = std::make_shared<sensor_msgs::Imu>();
  msg->header.stamp = ros::Time::fromSec(frame.timestamp);
  msg->header.frame_id = frame.frame_id;
  msg->linear_acceleration.x = frame.linear_acceleration[0];
  msg->linear_acceleration.y = frame.linear_acceleration[1];
  msg->linear_acceleration.z = frame.linear_acceleration[2];
  msg->angular_velocity.x = frame.angular_velocity[0];
  msg->angular_velocity.y = frame.angular_velocity[1];
  msg->angular_velocity.z = frame.angular_velocity[2];
  return msg;
}

sensor_msgs::Image::Ptr to_vendor_image(const ImageFrame& frame) {
  auto msg = std::make_shared<sensor_msgs::Image>();
  msg->header.stamp = ros::Time::fromSec(frame.timestamp);
  msg->header.frame_id = frame.frame_id;
  msg->encoding = frame.encoding;
  msg->width = static_cast<std::uint32_t>(frame.width);
  msg->height = static_cast<std::uint32_t>(frame.height);
  msg->data.resize(frame.payload_bytes);
  return msg;
}

sensor_msgs::PointCloud2::Ptr to_vendor_pointcloud2(const LidarFrame& frame) {
  auto msg = std::make_shared<sensor_msgs::PointCloud2>();
  msg->header.stamp = ros::Time::fromSec(frame.timestamp);
  msg->header.frame_id = frame.frame_id;
  msg->width = static_cast<std::uint32_t>(frame.point_count);
  msg->height = 1;
  return msg;
}

nav_msgs::Odometry to_vendor_odometry(const OdometryFrame& frame) {
  nav_msgs::Odometry msg;
  msg.header.stamp = ros::Time::fromSec(frame.timestamp);
  msg.header.frame_id = frame.frame_id;
  msg.child_frame_id = frame.child_frame_id;
  msg.pose.pose.position.x = frame.x;
  msg.pose.pose.position.y = frame.y;
  msg.pose.pose.position.z = frame.z;
  return msg;
}

ImuFrame from_vendor_imu(const sensor_msgs::Imu::ConstPtr& msg) {
  ImuFrame frame{};
  frame.timestamp = msg ? msg->header.stamp.toSec() : 0.0;
  frame.frame_id = msg ? msg->header.frame_id : "imu";
  if (msg) {
    frame.linear_acceleration = {msg->linear_acceleration.x, msg->linear_acceleration.y, msg->linear_acceleration.z};
    frame.angular_velocity = {msg->angular_velocity.x, msg->angular_velocity.y, msg->angular_velocity.z};
  }
  return frame;
}

ImageFrame from_vendor_image(const sensor_msgs::ImageConstPtr& msg) {
  ImageFrame frame{};
  frame.timestamp = msg ? msg->header.stamp.toSec() : 0.0;
  frame.frame_id = msg ? msg->header.frame_id : "camera";
  frame.encoding = msg ? msg->encoding : "compressed";
  frame.width = msg ? msg->width : 0;
  frame.height = msg ? msg->height : 0;
  frame.payload_bytes = msg ? msg->data.size() : 0;
  frame.compressed = frame.encoding.find("compressed") != std::string::npos;
  return frame;
}

LidarFrame from_vendor_pointcloud2(const sensor_msgs::PointCloud2::ConstPtr& msg) {
  LidarFrame frame{};
  frame.timestamp = msg ? msg->header.stamp.toSec() : 0.0;
  frame.frame_id = msg ? msg->header.frame_id : "lidar";
  frame.point_count = msg ? static_cast<std::size_t>(msg->width) * static_cast<std::size_t>(msg->height == 0 ? 1 : msg->height) : 0;
  return frame;
}

}  // namespace fastlivo_port
