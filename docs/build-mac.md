# Build on Mac mini (Apple Silicon)

## Goals

- keep the target runtime ROS-free
- use root CMake for native code
- use uv for Python-side orchestration and conversion tooling

## Current implementation

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

With the default options, this builds:

- `fastlivo_port_core` — portable replay/runtime scaffold
- `fastlivo_replay_runner` — end-to-end sequence consumer for replay smoke
- `fastlivo_vendor_shim_replay` — vendor-shaped callback smoke binary for the future `LIVMapper` boundary

## Dependency policy

- installable Python/userland packages: manage with `uv`
- pinned/native dependencies (SDKs, PCL, etc.): source builds are acceptable
- minimal ROS installation is allowed **only** for offline rosbag conversion

## Next native dependency work

When the actual FAST-LIVO2 core gets wired into this scaffold, the likely native dependency inventory is:

- Eigen
- OpenCV
- PCL
- Sophus
- Livox-SDK2

This scaffold intentionally keeps those out of the default smoke build so that local verification remains reproducible even before full native integration lands.

In other words: the repo already preserves the callback/API seam for the eventual FAST-LIVO2 core handoff, but the default Apple Silicon smoke path is still intentionally using the portable scaffold rather than the full upstream mapper/runtime.
