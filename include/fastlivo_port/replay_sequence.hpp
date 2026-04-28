#pragma once

#include "fastlivo_port/messages.hpp"
#include "fastlivo_port/portable_livmapper_adapter.hpp"
#include "fastlivo_port/portable_livo_core.hpp"

#include <string>
#include <vector>

namespace fastlivo_port {

enum class ReplayBackend {
  PortableCore,
  LivmapperAdapter,
};

struct ReplayResult {
  PortableLivoSummary summary{};
  std::vector<OdometryFrame> emitted_odometry{};
};

ReplayBackend parse_replay_backend(const std::string& value);
const char* replay_backend_name(ReplayBackend backend);
ReplayResult replay_sequence_file(const std::string& sequence_path,
                                  ReplayBackend backend = ReplayBackend::PortableCore,
                                  PortableLivoConfig config = {});

}  // namespace fastlivo_port
