# FAST-LIVO2-mini

Replay-first Mac mini / DimOS scaffold for porting FAST-LIVO2 away from ROS.

This scaffold now also includes a **vendor-shim conversion layer** so portable replay records can be converted into ROS/Livox-like compatibility structs without pulling ROS into the target runtime.

## Current state

This repo now contains:

- a **ROS-free portable runtime skeleton** for LiDAR + IMU + camera replay validation
- a **vendor-shim callback adapter** (`PortableLIVMapperAdapter`) that preserves the future `LIVMapper`-style integration boundary without requiring ROS in the smoke path
- a root **CMake** entrypoint for local smoke builds
- a root **uv** project scaffold for Python-side conversion / replay tooling
- offline **rosbag -> sequence** conversion utilities (minimal ROS install allowed for this step only)
- replay verification tooling that checks a sequence can be fully consumed and emits local odometry CSV output

The default build still uses the portable scaffold/runtime for smoke validation. It does **not** link the full upstream FAST-LIVO2 runtime yet; instead it keeps the replay-first path and the vendor-shaped callback boundary stable while the real core integration work continues.

## Quickstart

### 1. Build the portable replay runner

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

### 2. Bootstrap uv tooling

```bash
uv sync
```

If you want the local vendored DimOS package available through uv, install the optional robotics group:

```bash
uv sync --extra robotics
```

### 3. Verify the synthetic smoke fixture

Use the uv-managed interpreter so the replay tooling runs with the repo's Python 3.11+ requirement even if the system `python3` is older:

```bash
uv run python scripts/verify_sequence.py --sequence tests/fixtures/smoke_sequence.seq
uv run python scripts/run_replay.py --sequence tests/fixtures/smoke_sequence.seq --runner build/fastlivo_replay_runner
uv run python -m unittest discover -s tests/python
```

You can also validate the callback-style compatibility lane that mimics the future `LIVMapper` adapter boundary:

```bash
./build/fastlivo_vendor_shim_replay --sequence tests/fixtures/smoke_sequence.seq
```

## Replay smoke coverage

Today the replay smoke lane verifies:

- the sequence file contains IMU + image + lidar records and a terminal `END`
- synchronized measures can be rebuilt from the replay fixture
- the portable replay runner consumes the full sequence and emits odometry CSV
- the vendor-shaped callback shim still accepts replayed records through `imu_cbk`, `img_cbk`, and `standard_pcl_cbk`

This gives a stable offline validation path while the real FAST-LIVO2 core wiring remains in progress.

## Rosbag conversion

Your bag is expected to use **compressed image transport**. Convert it with:

```bash
uv run python scripts/rosbag_to_dimos.py \
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
uv run python scripts/sequence_to_dimos.py --sequence replay/my-sequence/sequence.seq --output replay/my-sequence/dimos-events.json
```

Inspect synchronized measure windows before connecting the real FAST-LIVO2 core:

```bash
uv run python scripts/inspect_measures.py --sequence replay/my-sequence/sequence.seq --output replay/my-sequence/measures.json
```

Or run the whole offline replay pipeline in one command once the rosbag is present:

```bash
uv run python scripts/full_replay_pipeline.py --bag /path/to/file.bag --replay-dir replay/my-sequence --runner build/fastlivo_replay_runner
```

## Planning artifacts

- PRD: `.omx/plans/prd-macmini-dimos-fastlivo2-port.md`
- Test spec: `.omx/plans/test-spec-macmini-dimos-fastlivo2-port.md`
- Deep interview spec: `.omx/specs/deep-interview-macmini-dimos-fastlivo2-uv.md`
