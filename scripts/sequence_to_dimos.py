from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "python"))

from fastlivo_port.dimos_bridge import sequence_to_bridge_events


def _payload_to_jsonable(payload: object) -> dict[str, object]:
    if isinstance(payload, dict):
        return payload
    if hasattr(payload, "__dict__"):
        return dict(payload.__dict__)
    if hasattr(payload, "__slots__"):
        return {slot: getattr(payload, slot) for slot in payload.__slots__}
    return {"repr": repr(payload)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Project a replay sequence into DimOS-oriented topic/message events")
    parser.add_argument("--sequence", required=True)
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    events = sequence_to_bridge_events(args.sequence)
    serializable = [
        {
            "topic": event.topic,
            "msg_type": event.msg_type,
            "timestamp": event.timestamp,
            "payload": _payload_to_jsonable(event.payload),
        }
        for event in events
    ]
    if args.output:
        Path(args.output).write_text(json.dumps(serializable, indent=2) + "\n")
    else:
        print(json.dumps(serializable, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
