# Live Run Notes

This repo is not yet at the full live-sensor stage.

What is implemented today:

- replay-first runtime skeleton
- rosbag conversion path
- non-ROS replay verification path
- vendor-shaped callback adapter (`PortableLIVMapperAdapter`) plus shim replay executable to keep the future FAST-LIVO2 entrypoints testable offline

What still needs to be wired for the full live Mac mini milestone:

- Livox-SDK2 sensor adapter
- camera adapter for the actual GigE/compressed feed
- DimOS transport bridge for live input channels
- the real FAST-LIVO2 algorithm/runtime behind the preserved portable/vendor callback boundary

Hardware sync remains an **external system assumption** owned by the separate MCU/fire-signal path, not this repo.
