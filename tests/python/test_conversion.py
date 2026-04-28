from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.conversion import _normalize_encoding_token


class ConversionTests(unittest.TestCase):
    def test_normalize_encoding_token_replaces_whitespace(self) -> None:
        self.assertEqual(_normalize_encoding_token("rgb8; jpeg compressed bgr8", "compressed"), "rgb8;_jpeg_compressed_bgr8")

    def test_normalize_encoding_token_uses_fallback(self) -> None:
        self.assertEqual(_normalize_encoding_token("", "compressed"), "compressed")


if __name__ == "__main__":
    unittest.main()
