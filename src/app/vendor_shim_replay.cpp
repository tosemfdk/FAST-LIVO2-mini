#include "fastlivo_port/replay_sequence.hpp"

#include <iostream>
#include <string>
using fastlivo_port::ReplayBackend;
using fastlivo_port::SequenceError;

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

}  // namespace

int main(int argc, char** argv) {
  try {
    const auto options = parse_args(argc, argv);
    const auto result = fastlivo_port::replay_sequence_file(options.sequence_path, ReplayBackend::LivmapperAdapter);
    const auto summary = result.summary;
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
