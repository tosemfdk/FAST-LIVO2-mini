#include "fastlivo_port/replay_sequence.hpp"

#include "fastlivo_port/vendor_conversions.hpp"

#include <fstream>
#include <sstream>
#include <stdexcept>

namespace fastlivo_port {

namespace {

std::vector<std::string> split_ws(const std::string& line) {
  std::istringstream stream(line);
  std::vector<std::string> tokens;
  std::string token;
  while (stream >> token) {
    tokens.push_back(token);
  }
  return tokens;
}

ImuFrame parse_imu_frame(const std::vector<std::string>& tokens) {
  if (tokens.size() != 9) {
    throw std::runtime_error("IMU line must have 9 tokens");
  }
  ImuFrame frame{};
  frame.timestamp = std::stod(tokens[1]);
  frame.frame_id = tokens[2];
  frame.linear_acceleration = {std::stod(tokens[3]), std::stod(tokens[4]), std::stod(tokens[5])};
  frame.angular_velocity = {std::stod(tokens[6]), std::stod(tokens[7]), std::stod(tokens[8])};
  return frame;
}

ImageFrame parse_image_frame(const std::vector<std::string>& tokens) {
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
  return frame;
}

LidarFrame parse_lidar_frame(const std::vector<std::string>& tokens) {
  if (tokens.size() != 4) {
    throw std::runtime_error("LIDAR line must have 4 tokens");
  }
  LidarFrame frame{};
  frame.timestamp = std::stod(tokens[1]);
  frame.frame_id = tokens[2];
  frame.point_count = static_cast<std::size_t>(std::stoul(tokens[3]));
  return frame;
}

double parse_end_timestamp(const std::vector<std::string>& tokens) {
  if (tokens.size() != 2) {
    throw std::runtime_error("END line must have 2 tokens");
  }
  return std::stod(tokens[1]);
}

}  // namespace

ReplayBackend parse_replay_backend(const std::string& value) {
  if (value == "portable-core") {
    return ReplayBackend::PortableCore;
  }
  if (value == "livmapper-adapter") {
    return ReplayBackend::LivmapperAdapter;
  }
  throw std::runtime_error("unknown replay backend: " + value);
}

const char* replay_backend_name(ReplayBackend backend) {
  switch (backend) {
    case ReplayBackend::PortableCore:
      return "portable-core";
    case ReplayBackend::LivmapperAdapter:
      return "livmapper-adapter";
  }
  return "unknown";
}

ReplayResult replay_sequence_file(const std::string& sequence_path,
                                  ReplayBackend backend,
                                  PortableLivoConfig config) {
  std::ifstream input(sequence_path);
  if (!input) {
    throw std::runtime_error("failed to open sequence: " + sequence_path);
  }

  PortableLivoCore core(config);
  PortableLIVMapperAdapter adapter(config);
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
      const auto frame = parse_imu_frame(tokens);
      if (backend == ReplayBackend::PortableCore) {
        core.push_imu(frame);
      } else {
        adapter.imu_cbk(to_vendor_imu(frame));
      }
      continue;
    }
    if (kind == "IMAGE") {
      const auto frame = parse_image_frame(tokens);
      if (backend == ReplayBackend::PortableCore) {
        core.push_image(frame);
      } else {
        adapter.img_cbk(to_vendor_image(frame));
      }
      continue;
    }
    if (kind == "LIDAR") {
      const auto frame = parse_lidar_frame(tokens);
      if (backend == ReplayBackend::PortableCore) {
        core.push_lidar(frame);
      } else {
        adapter.standard_pcl_cbk(to_vendor_pointcloud2(frame));
      }
      continue;
    }
    if (kind == "END") {
      const auto end_timestamp = parse_end_timestamp(tokens);
      if (backend == ReplayBackend::PortableCore) {
        core.finish(end_timestamp);
      } else {
        adapter.finish_sequence(end_timestamp);
      }
      continue;
    }
    throw std::runtime_error("unknown record kind: " + kind);
  }

  ReplayResult result;
  if (backend == ReplayBackend::PortableCore) {
    result.summary = core.summary();
    result.emitted_odometry = core.emitted_odometry();
  } else {
    result.summary = adapter.summary();
    result.emitted_odometry = adapter.emitted_odometry();
  }
  return result;
}

}  // namespace fastlivo_port
