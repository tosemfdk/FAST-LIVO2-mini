#include "fastlivo_port/replay_sequence.hpp"

#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

using fastlivo_port::PortableLivoSummary;
using fastlivo_port::ReplayBackend;
using fastlivo_port::ReplayResult;
using fastlivo_port::SequenceError;

namespace {

struct CliOptions {
  ReplayBackend backend{ReplayBackend::PortableCore};
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
    if (arg == "--backend" && index + 1 < argc) {
      options.backend = fastlivo_port::parse_replay_backend(argv[++index]);
      continue;
    }
    if (arg == "--odometry-out" && index + 1 < argc) {
      options.odometry_out = argv[++index];
      continue;
    }
    if (arg == "--help") {
      std::cout << "Usage: fastlivo_replay_runner --sequence <path> [--backend portable-core|livmapper-adapter] [--odometry-out <path>]\n";
      std::exit(0);
    }
    throw std::runtime_error("unknown argument: " + arg);
  }
  if (options.sequence_path.empty()) {
    throw std::runtime_error("--sequence is required");
  }
  return options;
}

void write_odometry_csv(const std::string& path, const ReplayResult& result) {
  if (path.empty()) {
    return;
  }
  std::ofstream out(path);
  out << "timestamp,x,y,z\n";
  for (const auto& odom : result.emitted_odometry) {
    out << std::fixed << std::setprecision(6) << odom.timestamp << ',' << odom.x << ',' << odom.y
        << ',' << odom.z << "\n";
  }
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const auto options = parse_args(argc, argv);
    const ReplayResult result = fastlivo_port::replay_sequence_file(options.sequence_path, options.backend);
    const PortableLivoSummary summary = result.summary;
    if (!summary.runtime.saw_end_marker) {
      throw std::runtime_error("sequence is missing END marker");
    }
    if (summary.runtime.odometry_count == 0) {
      throw std::runtime_error("sequence produced no odometry output");
    }

    write_odometry_csv(options.odometry_out, result);

    std::cout << "backend=" << fastlivo_port::replay_backend_name(options.backend)
              << " consumed_full_sequence=" << (summary.runtime.consumed_full_sequence ? "true" : "false")
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
