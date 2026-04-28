#pragma once

#include <array>
#include <cstddef>
#include <string>

namespace fastlivo_port {

struct ImuFrame {
  double timestamp{};
  std::string frame_id{"imu"};
  std::array<double, 3> linear_acceleration{};
  std::array<double, 3> angular_velocity{};
};

struct ImageFrame {
  double timestamp{};
  std::string frame_id{"camera"};
  std::string encoding{"compressed"};
  std::size_t width{};
  std::size_t height{};
  std::size_t payload_bytes{};
  bool compressed{true};
};

struct LidarFrame {
  double timestamp{};
  std::string frame_id{"lidar"};
  std::size_t point_count{};
};

struct OdometryFrame {
  double timestamp{};
  std::string frame_id{"odom"};
  std::string child_frame_id{"base_link"};
  double x{};
  double y{};
  double z{};
};

struct RuntimeSummary {
  std::size_t imu_count{};
  std::size_t image_count{};
  std::size_t lidar_count{};
  std::size_t odometry_count{};
  bool saw_end_marker{false};
  bool consumed_full_sequence{false};
  double latest_timestamp{};
};

}  // namespace fastlivo_port
