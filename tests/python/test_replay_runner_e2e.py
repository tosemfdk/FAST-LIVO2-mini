from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.replay import verify_sequence


COMMON_CPP_SOURCES = [
    "src/core/replay_sequence.cpp",
    "src/core/portable_runtime.cpp",
    "src/core/synchronizer.cpp",
    "src/core/portable_livo_core.cpp",
    "src/core/vendor_conversions.cpp",
    "src/core/portable_livmapper_adapter.cpp",
]


def _compile_binary(output_path: Path, app_source: str) -> None:
    compiler = shutil.which("clang++") or shutil.which("g++")
    if compiler is None:
        raise unittest.SkipTest("no C++ compiler available for replay e2e test")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        compiler,
        "-std=c++17",
        "-I",
        str(ROOT / "include"),
        *[str(ROOT / source) for source in COMMON_CPP_SOURCES],
        str(ROOT / app_source),
        "-o",
        str(output_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)


class ReplayRunnerE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.build_dir = ROOT / "build" / "test-e2e"
        cls.replay_runner = cls.build_dir / "fastlivo_replay_runner"
        cls.vendor_runner = cls.build_dir / "fastlivo_vendor_shim_replay"
        _compile_binary(cls.replay_runner, "src/app/fastlivo_runner.cpp")
        _compile_binary(cls.vendor_runner, "src/app/vendor_shim_replay.cpp")

    def test_replay_runner_consumes_smoke_fixture_and_writes_odometry(self) -> None:
        odometry_path = self.build_dir / "smoke_e2e_odometry.csv"
        result = verify_sequence(
            ROOT / "tests/fixtures/smoke_sequence.seq",
            runner=self.replay_runner,
            odometry_out=odometry_path,
        )

        self.assertEqual(result.stats.imu_count, 2)
        self.assertEqual(result.stats.image_count, 2)
        self.assertEqual(result.stats.lidar_count, 2)
        self.assertTrue(result.stats.saw_end)
        self.assertIn("consumed_full_sequence=true", result.stdout)
        self.assertIn("odom=3", result.stdout)

        csv_lines = odometry_path.read_text().strip().splitlines()
        self.assertEqual(csv_lines[0], "timestamp,x,y,z")
        self.assertEqual(len(csv_lines), 4)
        self.assertEqual(csv_lines[-1], "0.060000,0.200000,0.020000,0.002000")

    def test_vendor_shim_replay_keeps_smoke_path_alive(self) -> None:
        completed = subprocess.run(
            [
                str(self.vendor_runner),
                "--sequence",
                str(ROOT / "tests/fixtures/smoke_sequence.seq"),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        stdout = completed.stdout.strip()
        self.assertIn("shim_consumed_full_sequence=true", stdout)
        self.assertIn("measures=2", stdout)
        self.assertIn("odom=3", stdout)


if __name__ == "__main__":
    unittest.main()
