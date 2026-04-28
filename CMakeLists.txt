cmake_minimum_required(VERSION 3.20)
project(fast_livo2_mini LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(FASTLIVO_BUILD_PORTABLE_CORE "Build the ROS-free portable runtime skeleton" ON)
option(FASTLIVO_BUILD_VENDOR_ROS_LEGACY "Enable the original vendor ROS/catkin build" OFF)
option(FASTLIVO_BUILD_TESTS "Build local smoke tests" ON)

if(APPLE)
  add_compile_definitions(FASTLIVO_PLATFORM_APPLE=1)
  if(CMAKE_SYSTEM_PROCESSOR MATCHES "arm64|aarch64")
    add_compile_options(-O2)
  endif()
endif()

if(FASTLIVO_BUILD_PORTABLE_CORE)
  add_library(fastlivo_port_core
    src/core/portable_runtime.cpp
    src/core/synchronizer.cpp
    src/core/portable_livo_core.cpp
    src/core/vendor_conversions.cpp
    src/core/portable_livmapper_adapter.cpp
    src/core/replay_sequence.cpp
  )
  target_include_directories(fastlivo_port_core
    PUBLIC
      ${CMAKE_CURRENT_SOURCE_DIR}/include
  )
  target_compile_features(fastlivo_port_core PUBLIC cxx_std_17)

  add_executable(fastlivo_replay_runner
    src/app/fastlivo_runner.cpp
  )
  target_link_libraries(fastlivo_replay_runner PRIVATE fastlivo_port_core)

  add_executable(fastlivo_vendor_shim_replay
    src/app/vendor_shim_replay.cpp
  )
  target_link_libraries(fastlivo_vendor_shim_replay PRIVATE fastlivo_port_core)
endif()

if(FASTLIVO_BUILD_TESTS AND FASTLIVO_BUILD_PORTABLE_CORE)
  enable_testing()
  add_test(
    NAME fastlivo_replay_smoke
    COMMAND fastlivo_replay_runner
      --sequence ${CMAKE_CURRENT_SOURCE_DIR}/tests/fixtures/smoke_sequence.seq
      --odometry-out ${CMAKE_CURRENT_BINARY_DIR}/smoke_odometry.csv
  )
endif()

if(FASTLIVO_BUILD_VENDOR_ROS_LEGACY)
  add_subdirectory(src/thirdparty/FAST-LIVO2)
endif()
