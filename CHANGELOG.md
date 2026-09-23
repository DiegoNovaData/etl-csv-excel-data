# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Planned
- Migrate data contracts from YAML documentation to Pydantic models enforced
  at runtime (see [ADR 0004](docs/adr/0004-data-contracts-approach.md)).
- Historical/trend analysis (SCD2-style, keyed on `(product_id, extracted_at)`
  across retained snapshots) — current pipeline is current-state only.

## [0.2.0] - 2026-09-22
### Added
- Transform stage (`src/transform/transform_products.py`): flattens the
  latest raw snapshot into four normalized tables (`products`,
  `product_reviews`, `product_tags`, `product_images`), computes derived
  columns (`price_with_discount`, `review_count`, `avg_review_rating`), and
  writes them to `data/processed/`.
- Data quality validation with Great Expectations, in-code/ephemeral
  (`src/quality/expectations.py`): critical checks abort the Transform run,
  warning checks are logged only.
- Load stage (`src/load/load_products.py`): promotes validated tables from
  `data/processed/` to `data/output/` as CSV, plus a `manifest.json` with
  load timestamp and row counts.
- Data contracts (`contracts/*.contract.yaml`) for all four output tables,
  following the Data Contract Specification.
- Entity-relationship diagram (`docs/entity-relationship-diagram.md`)
  describing the four-table schema and how to replicate it in a real
  database.
- Two new ADRs: data contracts approach (0004), data quality with Great
  Expectations (0005).
- Transform and Load runbooks.
- Unit tests for Transform, Load, and the Great Expectations suites (13 new
  tests).

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
