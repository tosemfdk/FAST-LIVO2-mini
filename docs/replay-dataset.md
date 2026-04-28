# Replay Dataset Workflow

## Intended source

The primary validation dataset is a user-provided rosbag hosted outside the repo.

## Policy

- do not commit the rosbag into the repo
- keep fetch/storage instructions separate from source control
- convert bag data into a local replay directory with:
  - `sequence.seq`
  - `manifest.json`

## Example

```bash
python3 scripts/rosbag_to_dimos.py \
  --bag ~/Downloads/my_capture.bag \
  --output-dir replay/my_capture \
  --image-topic /camera/image/compressed \
  --imu-topic /imu/data \
  --lidar-topic /points_raw
```
