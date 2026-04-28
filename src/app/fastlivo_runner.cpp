#include "fastlivo_port/portable_livo_core.hpp"

#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using fastlivo_port::ImageFrame;
using fastlivo_port::ImuFrame;
using fastlivo_port::LidarFrame;
using fastlivo_port::PortableLivoCore;
using fastlivo_port::PortableLivoSummary;
using fastlivo_port::SequenceError;

namespace {

struct CliOptions {
  std::string sequence_path;
  std::string odometry_out;
};

CliOptions parse_args(int argc, char** argv) {
  CliOptions options;
  for (int index = 1; index < argc; ++index) {
    const std::string arg = argv[index];
    if (arg == "--sequence" && index + 1 < argc) {
      options.sequence_path = argv[++index];
      continue;
    }
    if (arg == "--odometry-out" && index + 1 < argc) {
      options.odometry_out = argv[++index];
      continue;
    }
    if (arg == "--help") {
      std::cout << "Usage: fastlivo_replay_runner --sequence <path> --odometry-out <path>\n";
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

void write_odometry_csv(const std::string& path, const PortableLivoCore& runtime) {
  if (path.empty()) {
    return;
  }
  std::ofstream out(path);
  out << "timestamp,x,y,z\n";
  for (const auto& odom : runtime.emitted_odometry()) {
    out << std::fixed << std::setprecision(6) << odom.timestamp << ',' << odom.x << ',' << odom.y
        << ',' << odom.z << "\n";
  }
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const auto options = parse_args(argc, argv);
    std::ifstream input(options.sequence_path);
    if (!input) {
      throw std::runtime_error("failed to open sequence: " + options.sequence_path);
    }

    PortableLivoCore core;
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
        if (tokens.size() != 9) {
          throw std::runtime_error("IMU line must have 9 tokens");
        }
        ImuFrame frame{};
        frame.timestamp = std::stod(tokens[1]);
        frame.frame_id = tokens[2];
        frame.linear_acceleration = {std::stod(tokens[3]), std::stod(tokens[4]), std::stod(tokens[5])};
        frame.angular_velocity = {std::stod(tokens[6]), std::stod(tokens[7]), std::stod(tokens[8])};
        core.push_imu(frame);
      } else if (kind == "IMAGE") {
        if (tokens.size() != 7) {
          throw std::runtime_error("IMAGE line must have 7 tokens");
        }
        ImageFrame frame{};
        frame.timestamp = std::stod(tokens[1]);
        frame.frame_id = tokens[2];
        frame.encoding = tokens[3];
        frame.width = static_cast<std::size_t>(std::stoul(tokens[4]));
        frame.height = static_cast<std::size_t>(std::stoul(tokens[5]));
        frame.payload_bytes = static_cast<std::size_t>(std::stoul(tokens[6]));
        frame.compressed = frame.encoding.find("compressed") != std::string::npos;
        core.push_image(frame);
      } else if (kind == "LIDAR") {
        if (tokens.size() != 4) {
          throw std::runtime_error("LIDAR line must have 4 tokens");
        }
        LidarFrame frame{};
        frame.timestamp = std::stod(tokens[1]);
        frame.frame_id = tokens[2];
        frame.point_count = static_cast<std::size_t>(std::stoul(tokens[3]));
        core.push_lidar(frame);
      } else if (kind == "END") {
        if (tokens.size() != 2) {
          throw std::runtime_error("END line must have 2 tokens");
        }
        core.finish(std::stod(tokens[1]));
      } else {
        throw std::runtime_error("unknown record kind: " + kind);
      }
    }

    const PortableLivoSummary summary = core.summary();
    if (!summary.runtime.saw_end_marker) {
      throw std::runtime_error("sequence is missing END marker");
    }
    if (summary.runtime.odometry_count == 0) {
      throw std::runtime_error("sequence produced no odometry output");
    }

    write_odometry_csv(options.odometry_out, core);

    std::cout << "consumed_full_sequence=" << (summary.runtime.consumed_full_sequence ? "true" : "false")
              << " imu=" << summary.runtime.imu_count << " image=" << summary.runtime.image_count
              << " lidar=" << summary.runtime.lidar_count << " odom=" << summary.runtime.odometry_count
              << " measures=" << summary.sync.measure_count
              << " lidar_without_image=" << summary.sync.lidar_without_image
              << " empty_imu_windows=" << summary.sync.empty_imu_windows << '\n';
    return 0;
  } catch (const SequenceError& error) {
    std::cerr << "sequence error: " << error.what() << '\n';
  } catch (const std::exception& error) {
    std::cerr << "error: " << error.what() << '\n';
  }
  return 1;
}
