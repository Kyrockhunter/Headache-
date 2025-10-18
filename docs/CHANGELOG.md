# FantasyV4 Changelog

## [v4.1.1] — 2025-10-18
### Added
- `build_week_via_master.py` wrapper for robust weekly dataset generation.
- Adaptive ingestion (v7) capable of detecting nflreadpy argument variations automatically.
- Logging improvements for clarity in data load and file save operations.

### Changed
- Simplified data retrieval pipeline to rely on stable local `weekly_master` builds.
- Updated project directory references (`ROOTDIR`, `DATA_PROCESSED`, `LOG_FILE`) for universal compatibility.

### Fixed
- Eliminated dataset duplication issue during multiple same-week pulls (pending idempotent merge v2).
- Corrected path resolution fallback when `root_dir` not explicitly defined in `settings.yaml`.

### Next Step
- Implement `historical_merge v2` to ensure week-level deduplication and replacement safety.
