# FAST-LIVO2-mini

Replay-first Mac mini / DimOS scaffold for porting FAST-LIVO2 away from ROS.

This scaffold now also includes a **vendor-shim conversion layer** so portable replay records can be converted into ROS/Livox-like compatibility structs without pulling ROS into the target runtime.

## Current state

This repo now contains:

- a **ROS-free portable runtime skeleton** for LiDAR + IMU + camera replay validation
- a root **CMake** entrypoint for local smoke builds
- a root **uv** project scaffold for Python-side conversion / replay tooling
- offline **rosbag -> sequence** conversion utilities (minimal ROS install allowed for this step only)
- replay verification tooling that checks a sequence can be fully consumed and emits local odometry CSV output

## Quickstart

### 1. Build the portable replay runner

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

### 2. Verify the synthetic smoke fixture

```bash
python3 scripts/verify_sequence.py --sequence tests/fixtures/smoke_sequence.seq
python3 scripts/run_replay.py --sequence tests/fixtures/smoke_sequence.seq --runner build/fastlivo_replay_runner
```

You can also validate the callback-style compatibility lane that mimics the future `LIVMapper` adapter boundary:

```bash
./build/fastlivo_vendor_shim_replay --sequence tests/fixtures/smoke_sequence.seq
```

### 3. Bootstrap uv tooling

```bash
uv sync
```

If you want the local vendored DimOS package available through uv, install the optional robotics group:

```bash
uv sync --extra robotics
```

## Rosbag conversion

Your bag is expected to use **compressed image transport**. Convert it with:

```bash
python3 scripts/rosbag_to_dimos.py \
  --bag /path/to/file.bag \
  --output-dir replay/my-sequence \
  --image-topic /camera/image/compressed \
  --imu-topic /imu/data \
  --lidar-topic /points_raw \
  --image-transport compressed
```

This conversion path is intentionally **offline-only**. A minimal ROS install is acceptable here, but the target runtime path for the port remains non-ROS.

You can also project a converted sequence into DimOS-oriented topic events for inspection:

```bash
python3 scripts/sequence_to_dimos.py --sequence replay/my-sequence/sequence.seq --output replay/my-sequence/dimos-events.json
```

Inspect synchronized measure windows before connecting the real FAST-LIVO2 core:

```bash
python3 scripts/inspect_measures.py --sequence replay/my-sequence/sequence.seq --output replay/my-sequence/measures.json
```

Or run the whole offline replay pipeline in one command once the rosbag is present:

```bash
python3 scripts/full_replay_pipeline.py --bag /path/to/file.bag --replay-dir replay/my-sequence --runner build/fastlivo_replay_runner
```

## Planning artifacts

- PRD: `.omx/plans/prd-macmini-dimos-fastlivo2-port.md`
- Test spec: `.omx/plans/test-spec-macmini-dimos-fastlivo2-port.md`
- Deep interview spec: `.omx/specs/deep-interview-macmini-dimos-fastlivo2-uv.md`
