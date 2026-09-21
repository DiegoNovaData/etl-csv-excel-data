# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Planned
- Transform stage: flatten/normalize raw JSON into tabular data, data quality
  checks.
- Load stage: produce CSV/Excel deliverables in `data/output/`.

## [0.1.0] - 2026-09-20
### Added
- Initial project scaffolding (`config/`, `data/`, `docs/`, `notebooks/`,
  `scripts/`, `src/`, `tests/`).
- Extract stage: fetch the retail product catalog from the DummyJSON public
  API (`src/extract/extract_dummyjson.py`), with pagination, retry/backoff,
  and timestamped raw JSON snapshots.
- Shared logging utility (`src/utils/logger.py`) writing to `logs/etl.log`.
- Configuration file (`config/config.yaml`) for source and path settings.
- Unit tests for the extraction module (`tests/test_extract_dummyjson.py`).
- Project documentation: bilingual README, ADRs (0001–0003), extract runbook,
  data lineage, and data dictionary.
