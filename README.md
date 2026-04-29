# FAST-LIVO2-mini

[English](#english) | [한국어](#한국어)

---

## English

### Overview

`FAST-LIVO2-mini` is a replay-first scaffold for porting FAST-LIVO2 to a **Mac mini / Apple Silicon / non-ROS** runtime while keeping the long-term target aligned with **LiDAR + IMU + Camera** input and a **DimOS / LCM** transport boundary.

Today, this repository is primarily a **validation and bridging workspace**:

- a **ROS-free portable replay runtime** exists for smoke validation
- a **vendor-shaped callback adapter** (`PortableLIVMapperAdapter`) preserves the future `LIVMapper` integration boundary
- Python tools can convert offline bag data into the repository replay format
- ROS2 rosbag2 (`.db3`) data can now be bridged into **DimOS-style LCM channels**

This is **not** yet a full upstream FAST-LIVO2 runtime port. The real estimator integration and live calibrated sensor path are still in progress.

### What is verified right now

#### Replay scaffold

The current replay path can:

- read replay sequences containing **IMU + image + lidar + END**
- rebuild synchronized measures from the sequence
- consume the full sequence in:
  - `portable-core` mode
  - `livmapper-adapter` mode
- emit local odometry CSV output from the scaffold runtime

#### Real bag validation

A real downloaded dataset was validated locally:

- input format: **ROS2 rosbag2 / sqlite3**
- files:
  - `4_28_handheld_0.db3`
  - `metadata.yaml`
- detected topics:
  - `/livox/lidar`
  - `/livox/imu`
  - `/camera/camera/color/image_raw/compressed`

Converted replay stats:

- IMU: `236747`
- Image: `35541`
- LiDAR: `11838`
- terminal END marker: `true`

Validated replay results:

- `portable-core` → `consumed_full_sequence=true`
- `livmapper-adapter` → `consumed_full_sequence=true`
- `vendor_shim` → `shim_consumed_full_sequence=true`

### Quickstart

#### 1. Build the replay binaries

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

#### 2. Install Python tooling

```bash
uv sync
```

Optional extras:

```bash
uv sync --extra robotics
uv sync --extra dimos-bridge
```

- `robotics`: local vendored DimOS package
- `dimos-bridge`: ROS2 bag → DimOS-style LCM bridge helpers

#### 3. Run the synthetic smoke fixture

```bash
uv run python scripts/verify_sequence.py --sequence tests/fixtures/smoke_sequence.seq
uv run python scripts/run_replay.py --sequence tests/fixtures/smoke_sequence.seq --runner build/fastlivo_replay_runner
uv run python -m unittest discover -s tests/python
```

Optional vendor-shaped callback lane:

```bash
./build/fastlivo_vendor_shim_replay --sequence tests/fixtures/smoke_sequence.seq
```

### Offline bag conversion

#### ROS1 `.bag`

```bash
uv run python scripts/rosbag_to_dimos.py \
  --bag /path/to/file.bag \
  --output-dir replay/my-sequence \
  --image-topic /camera/image/compressed \
  --imu-topic /imu/data \
  --lidar-topic /points_raw \
  --image-transport compressed
```

#### ROS2 rosbag2 `.db3`

You can point the same converter at the `.db3` file or its containing directory:

```bash
uv run python scripts/rosbag_to_dimos.py \
  --bag /path/to/recording_0.db3 \
  --output-dir replay/my-sequence
```

Useful follow-up tools:

```bash
uv run python scripts/sequence_to_dimos.py --sequence replay/my-sequence/sequence.seq --output replay/my-sequence/dimos-events.json
uv run python scripts/inspect_measures.py --sequence replay/my-sequence/sequence.seq --output replay/my-sequence/measures.json
uv run python scripts/full_replay_pipeline.py --bag /path/to/file.bag --replay-dir replay/my-sequence --runner build/fastlivo_replay_runner
```

### DimOS LCM bridge

For ROS2 rosbag2 sqlite3 recordings, the repository can now publish the bag onto **DimOS-style LCM channels**.

```bash
python3 scripts/play_dimos_lcm.py \
  --bag replay/drive_4_28_handheld/4_28_handheld_0.db3 \
  --lcm-url memq:// \
  --max-messages 120
```

Default channels:

- `/fastlivo/imu#sensor_msgs.Imu`
- `/fastlivo/image/compressed#sensor_msgs.CompressedImage`
- `/fastlivo/lidar#sensor_msgs.PointCloud2`
- `/fastlivo/odometry#nav_msgs.Odometry`

LCM URL notes:

- `memq://` is useful for **in-process smoke tests**
- `udpm://...` is intended for **real interprocess / LAN playback**

### Current limitation on this Mac

The bridge works in `memq://` mode, but **real `udpm://...` LCM playback is not yet verified on this Mac**.

Evidence so far:

- in-process `memq://` publish/receive succeeded
- raw local-network UDP and LCM multicast on this Mac returned `No route to host`
- this points to a **host/network environment issue**, not a replay parsing failure

So the current status is:

- **confirmed**: bag → replay sequence → DimOS-style LCM message publishing path exists
- **confirmed**: `memq://` in-process smoke publishing works
- **not yet confirmed**: `udpm://...` interprocess delivery on this host

### What is still not done

- full upstream FAST-LIVO2 estimator integration
- live calibrated lidar/camera runtime path on Mac mini
- real downstream DimOS consumer validation against the published `/fastlivo/*` channels
- reliable interprocess multicast validation on this host

### Planning artifacts

- PRD: `.omx/plans/prd-macmini-dimos-fastlivo2-port.md`
- Test spec: `.omx/plans/test-spec-macmini-dimos-fastlivo2-port.md`
- Deep interview spec: `.omx/specs/deep-interview-macmini-dimos-fastlivo2-uv.md`

---

## 한국어

### 개요

`FAST-LIVO2-mini`는 FAST-LIVO2를 **Mac mini / Apple Silicon / 비-ROS** 런타임으로 포팅하기 위한 replay-first 스캐폴드다. 장기 목표는 **LiDAR + IMU + Camera** 입력을 유지하면서, 입출력 경계를 **DimOS / LCM** 쪽으로 옮기는 것이다.

현재 이 저장소는 주로 **검증 및 브릿지 작업용 워크스페이스**다.

- **ROS-free portable replay runtime** 이 있음
- 향후 `LIVMapper` 결합 지점을 유지하는 **vendor-shaped callback adapter** (`PortableLIVMapperAdapter`)가 있음
- 오프라인 bag 데이터를 repo replay 포맷으로 변환하는 Python 도구가 있음
- ROS2 rosbag2 (`.db3`) 데이터를 **DimOS-style LCM 채널**로 뿌릴 수 있음

다만 아직 **업스트림 FAST-LIVO2 전체 런타임 포트**는 아니다. 실제 추정기 결합과 live calibrated sensor path는 계속 진행 중이다.

### 지금 검증된 것

#### Replay scaffold

현재 replay 경로는 다음을 할 수 있다.

- **IMU + image + lidar + END** 를 포함한 sequence 파일 읽기
- sequence에서 synchronized measure 재구성
- 다음 두 모드에서 full sequence consume:
  - `portable-core`
  - `livmapper-adapter`
- scaffold runtime 기준 local odometry CSV 출력

#### 실제 bag 검증

실제로 내려받은 데이터셋으로 로컬 검증을 했다.

- 입력 포맷: **ROS2 rosbag2 / sqlite3**
- 파일:
  - `4_28_handheld_0.db3`
  - `metadata.yaml`
- 자동 탐지된 토픽:
  - `/livox/lidar`
  - `/livox/imu`
  - `/camera/camera/color/image_raw/compressed`

변환된 replay 통계:

- IMU: `236747`
- Image: `35541`
- LiDAR: `11838`
- END marker: `true`

replay 검증 결과:

- `portable-core` → `consumed_full_sequence=true`
- `livmapper-adapter` → `consumed_full_sequence=true`
- `vendor_shim` → `shim_consumed_full_sequence=true`

### 빠른 시작

#### 1. replay 바이너리 빌드

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

#### 2. Python 도구 설치

```bash
uv sync
```

옵션 extra:

```bash
uv sync --extra robotics
uv sync --extra dimos-bridge
```

- `robotics`: vendored DimOS 패키지 사용
- `dimos-bridge`: ROS2 bag → DimOS-style LCM bridge helper 사용

#### 3. synthetic smoke fixture 실행

```bash
uv run python scripts/verify_sequence.py --sequence tests/fixtures/smoke_sequence.seq
uv run python scripts/run_replay.py --sequence tests/fixtures/smoke_sequence.seq --runner build/fastlivo_replay_runner
uv run python -m unittest discover -s tests/python
```

vendor-shaped callback lane 확인:

```bash
./build/fastlivo_vendor_shim_replay --sequence tests/fixtures/smoke_sequence.seq
```

### 오프라인 bag 변환

#### ROS1 `.bag`

```bash
uv run python scripts/rosbag_to_dimos.py \
  --bag /path/to/file.bag \
  --output-dir replay/my-sequence \
  --image-topic /camera/image/compressed \
  --imu-topic /imu/data \
  --lidar-topic /points_raw \
  --image-transport compressed
```

#### ROS2 rosbag2 `.db3`

같은 변환기를 `.db3` 파일이나 그 디렉터리에 그대로 쓸 수 있다.

```bash
uv run python scripts/rosbag_to_dimos.py \
  --bag /path/to/recording_0.db3 \
  --output-dir replay/my-sequence
```

같이 쓸 수 있는 도구:

```bash
uv run python scripts/sequence_to_dimos.py --sequence replay/my-sequence/sequence.seq --output replay/my-sequence/dimos-events.json
uv run python scripts/inspect_measures.py --sequence replay/my-sequence/sequence.seq --output replay/my-sequence/measures.json
uv run python scripts/full_replay_pipeline.py --bag /path/to/file.bag --replay-dir replay/my-sequence --runner build/fastlivo_replay_runner
```

### DimOS LCM bridge

ROS2 rosbag2 sqlite3 recording을 **DimOS-style LCM 채널**로 publish할 수 있다.

```bash
python3 scripts/play_dimos_lcm.py \
  --bag replay/drive_4_28_handheld/4_28_handheld_0.db3 \
  --lcm-url memq:// \
  --max-messages 120
```

기본 채널:

- `/fastlivo/imu#sensor_msgs.Imu`
- `/fastlivo/image/compressed#sensor_msgs.CompressedImage`
- `/fastlivo/lidar#sensor_msgs.PointCloud2`
- `/fastlivo/odometry#nav_msgs.Odometry`

LCM URL 메모:

- `memq://` 는 **같은 프로세스 내부 smoke test** 용도
- `udpm://...` 는 **실제 프로세스 간 / LAN 재생** 용도

### 이 맥에서의 현재 제한

bridge 자체는 `memq://` 모드에서 동작하지만, **이 맥에서 실제 `udpm://...` LCM playback은 아직 검증되지 않았다.**

현재까지 확인한 근거:

- 같은 프로세스 내부 `memq://` publish/receive 는 성공
- 이 맥에서는 raw local-network UDP 와 LCM multicast 가 `No route to host` 로 실패
- 즉 replay 파서 문제가 아니라 **호스트/네트워크 환경 문제** 쪽으로 보임

그래서 현재 상태는:

- **확인됨**: bag → replay sequence → DimOS-style LCM message publishing 경로 존재
- **확인됨**: `memq://` 기반 in-process smoke publish 성공
- **아직 미확인**: 이 호스트에서 `udpm://...` 기반 프로세스 간 전달

### 아직 안 된 것

- 업스트림 FAST-LIVO2 실제 estimator 전체 결합
- Mac mini live calibrated lidar/camera runtime path
- publish된 `/fastlivo/*` 채널을 실제 downstream DimOS consumer가 먹는 검증
- 이 호스트에서 안정적인 interprocess multicast 검증

### 계획 문서

- PRD: `.omx/plans/prd-macmini-dimos-fastlivo2-port.md`
- Test spec: `.omx/plans/test-spec-macmini-dimos-fastlivo2-port.md`
- Deep interview spec: `.omx/specs/deep-interview-macmini-dimos-fastlivo2-uv.md`
