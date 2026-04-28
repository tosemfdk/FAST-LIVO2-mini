# Replay Validation

## First-pass success rule

The first success gate is not a live-Hz number. It is:

1. convert rosbag-derived data into this repo's replay sequence format
2. consume the **full sequence** end-to-end
3. emit **local odometry output**
4. require **no ROS runtime path** during replay execution

## File formats

### `sequence.seq`

Plain-text sequence file used by the portable replay runner.

Record forms:

- `IMU <ts> <frame_id> <ax> <ay> <az> <gx> <gy> <gz>`
- `IMAGE <ts> <frame_id> <encoding> <width> <height> <payload_bytes>`
- `LIDAR <ts> <frame_id> <point_count>`
- `END <ts>`

### `manifest.json`

Metadata emitted by `scripts/rosbag_to_dimos.py` for auditability.

## Commands

```bash
uv run python scripts/verify_sequence.py --sequence replay/example/sequence.seq
uv run python scripts/run_replay.py --sequence replay/example/sequence.seq --runner build/fastlivo_replay_runner
uv run python -m unittest discover -s tests/python
./build/fastlivo_vendor_shim_replay --sequence tests/fixtures/smoke_sequence.seq
```

## Current integration boundary

Replay validation currently covers two offline lanes:

1. `fastlivo_replay_runner` drives the portable scaffold directly and must consume the full sequence while emitting odometry output.
2. `fastlivo_vendor_shim_replay` pushes the same fixture through the vendor-shaped callback boundary (`imu_cbk`, `img_cbk`, `standard_pcl_cbk`) so the future FAST-LIVO2 core handoff can keep the same ingress shape.

This means replay smoke stays green even before the full upstream FAST-LIVO2 runtime is linked into the default build.

## Google Drive rosbag note

The user indicated the first real bag will arrive via Google Drive and that images are already stored as **compressed image** messages. The conversion script is written with that transport in mind.
