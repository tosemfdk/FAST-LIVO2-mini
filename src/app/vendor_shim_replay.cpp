#include "fastlivo_port/portable_livmapper_adapter.hpp"
#include "fastlivo_port/vendor_conversions.hpp"

#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using fastlivo_port::ImageFrame;
using fastlivo_port::ImuFrame;
using fastlivo_port::LidarFrame;
using fastlivo_port::PortableLIVMapperAdapter;
using fastlivo_port::SequenceError;
using fastlivo_port::to_vendor_image;
using fastlivo_port::to_vendor_imu;
using fastlivo_port::to_vendor_pointcloud2;

namespace {

struct CliOptions {
  std::string sequence_path;
};

CliOptions parse_args(int argc, char** argv) {
  CliOptions options;
  for (int index = 1; index < argc; ++index) {
    const std::string arg = argv[index];
    if (arg == "--sequence" && index + 1 < argc) {
      options.sequence_path = argv[++index];
      continue;
    }
    if (arg == "--help") {
      std::cout << "Usage: fastlivo_vendor_shim_replay --sequence <path>\n";
      std::exit(0);
    }
    throw std::runtime_error("unknown argument: " + arg);
  }
  if (options.sequence_path.empty()) {
    throw std::runtime_error("--sequence is required");
  }
  return options;
}

std::vector<std::string> split_ws(const std::string& line) {
  std::istringstream stream(line);
  std::vector<std::string> tokens;
  std::string token;
  while (stream >> token) {
    tokens.push_back(token);
  }
  return tokens;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const auto options = parse_args(argc, argv);
    std::ifstream input(options.sequence_path);
    if (!input) {
      throw std::runtime_error("failed to open sequence: " + options.sequence_path);
    }

    PortableLIVMapperAdapter adapter;
    std::string line;
    while (std::getline(input, line)) {
      if (line.empty() || line[0] == '#') {
        continue;
      }
      const auto tokens = split_ws(line);
      if (tokens.empty()) {
        continue;
      }
      const auto& kind = tokens[0];
      if (kind == "IMU") {
        ImuFrame frame{};
        frame.timestamp = std::stod(tokens[1]);
        frame.frame_id = tokens[2];
        frame.linear_acceleration = {std::stod(tokens[3]), std::stod(tokens[4]), std::stod(tokens[5])};
        frame.angular_velocity = {std::stod(tokens[6]), std::stod(tokens[7]), std::stod(tokens[8])};
        adapter.imu_cbk(to_vendor_imu(frame));
      } else if (kind == "IMAGE") {
        ImageFrame frame{};
        frame.timestamp = std::stod(tokens[1]);
        frame.frame_id = tokens[2];
        frame.encoding = tokens[3];
        frame.width = static_cast<std::size_t>(std::stoul(tokens[4]));
        frame.height = static_cast<std::size_t>(std::stoul(tokens[5]));
        frame.payload_bytes = static_cast<std::size_t>(std::stoul(tokens[6]));
        frame.compressed = frame.encoding.find("compressed") != std::string::npos;
        adapter.img_cbk(to_vendor_image(frame));
      } else if (kind == "LIDAR") {
        LidarFrame frame{};
        frame.timestamp = std::stod(tokens[1]);
        frame.frame_id = tokens[2];
        frame.point_count = static_cast<std::size_t>(std::stoul(tokens[3]));
        adapter.standard_pcl_cbk(to_vendor_pointcloud2(frame));
      } else if (kind == "END") {
        adapter.finish_sequence(std::stod(tokens[1]));
      }
    }

    const auto summary = adapter.summary();
    std::cout << "shim_consumed_full_sequence=" << (summary.runtime.consumed_full_sequence ? "true" : "false")
              << " measures=" << summary.sync.measure_count
              << " odom=" << summary.runtime.odometry_count << '\n';
    return 0;
  } catch (const SequenceError& error) {
    std::cerr << "sequence error: " << error.what() << '\n';
  } catch (const std::exception& error) {
    std::cerr << "error: " << error.what() << '\n';
  }
  return 1;
}
