#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <utility>
#include <vector>

namespace ros {

struct Time {
  double sec{0.0};

  Time() = default;
  explicit Time(double seconds) : sec(seconds) {}

  static Time now() { return Time{}; }
  static Time fromSec(double seconds) { return Time(seconds); }
  double toSec() const { return sec; }
};

struct TimerEvent {};
struct Publisher {};
struct Subscriber {};
struct Timer {};

class NodeHandle {
 public:
  template <typename T>
  void param(const std::string&, T& target, const T& default_value) const {
    target = default_value;
  }
};

inline void init(int, char**, const std::string&) {}

}  // namespace ros

namespace std_msgs {

struct Header {
  ros::Time stamp{};
  std::string frame_id{};
};

}  // namespace std_msgs

namespace geometry_msgs {

struct Vector3 {
  double x{0.0};
  double y{0.0};
  double z{0.0};
};

struct Quaternion {
  double x{0.0};
  double y{0.0};
  double z{0.0};
  double w{1.0};
};

struct Point {
  double x{0.0};
  double y{0.0};
  double z{0.0};
};

struct Pose {
  Point position{};
  Quaternion orientation{};
};

struct Twist {
  Vector3 linear{};
  Vector3 angular{};
};

struct PoseStamped {
  std_msgs::Header header{};
  Pose pose{};
};

}  // namespace geometry_msgs

namespace nav_msgs {

struct Path {
  std_msgs::Header header{};
  std::vector<geometry_msgs::PoseStamped> poses{};
};

struct Odometry {
  std_msgs::Header header{};
  std::string child_frame_id{};

  struct PoseContainer {
    geometry_msgs::Pose pose{};
  } pose{};

  struct TwistContainer {
    geometry_msgs::Twist twist{};
  } twist{};
};

}  // namespace nav_msgs

namespace sensor_msgs {

struct Imu {
  using Ptr = std::shared_ptr<Imu>;
  using ConstPtr = std::shared_ptr<const Imu>;

  std_msgs::Header header{};
  geometry_msgs::Quaternion orientation{};
  geometry_msgs::Vector3 angular_velocity{};
  geometry_msgs::Vector3 linear_acceleration{};
};

using ImuConstPtr = Imu::ConstPtr;

struct Image {
  using Ptr = std::shared_ptr<Image>;
  using ConstPtr = std::shared_ptr<const Image>;

  std_msgs::Header header{};
  std::string encoding{};
  std::uint32_t width{0};
  std::uint32_t height{0};
  std::vector<std::uint8_t> data{};
};

using ImageConstPtr = Image::ConstPtr;

struct PointCloud2 {
  using Ptr = std::shared_ptr<PointCloud2>;
  using ConstPtr = std::shared_ptr<const PointCloud2>;

  std_msgs::Header header{};
  std::uint32_t width{0};
  std::uint32_t height{0};
  std::vector<std::uint8_t> data{};
};

}  // namespace sensor_msgs

namespace visualization_msgs {

struct Marker {};
struct MarkerArray {};

}  // namespace visualization_msgs

namespace image_transport {

struct Publisher {};

class ImageTransport {
 public:
  explicit ImageTransport(ros::NodeHandle&) {}
  Publisher advertise(const std::string&, int) const { return Publisher{}; }
};

}  // namespace image_transport

namespace tf {

class Transform {};

class StampedTransform {
 public:
  StampedTransform(Transform, ros::Time, std::string, std::string) {}
};

class TransformBroadcaster {
 public:
  void sendTransform(const StampedTransform&) {}
};

}  // namespace tf

namespace livox_ros_driver {

struct CustomPoint {
  float x{0.F};
  float y{0.F};
  float z{0.F};
  float reflectivity{0.F};
  std::uint8_t tag{0};
  std::uint8_t line{0};
  double offset_time{0.0};
};

struct CustomMsg {
  using Ptr = std::shared_ptr<CustomMsg>;
  using ConstPtr = std::shared_ptr<const CustomMsg>;

  std_msgs::Header header{};
  std::uint32_t point_num{0};
  std::vector<CustomPoint> points{};
};

}  // namespace livox_ros_driver
