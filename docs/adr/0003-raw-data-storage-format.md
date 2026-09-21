# 0003. Store the raw layer as timestamped JSON snapshots

## Status
Accepted

## Context
The source API ([0002](0002-data-source-selection.md)) returns nested JSON
(objects like `dimensions` and `meta`, arrays like `reviews`, `tags`,
`images`). The raw layer's job is to preserve exactly what the source
returned, so that any transformation bug can be diagnosed against an
untouched copy of the source data, and so the Transform stage can decide how
to flatten/normalize the schema rather than losing information at extraction
time.

## Decision
- Persist each Extract run as a single JSON file in `data/raw/`, named
  `products_raw_<UTC_TIMESTAMP>.json`.
- Wrap the source records in a small envelope: `extracted_at`, `source`,
  `record_count`, `products`. This makes each raw file self-describing
  (when it was pulled, from where, how many records) without needing to
  cross-reference logs.
- Treat raw files as immutable and append-only across runs (never overwrite a
  previous snapshot); `data/raw/` is git-ignored so these snapshots stay local
  disk artifacts rather than repository history.

## Consequences
- Raw JSON is not directly analysis-friendly (nested structures, no tabular
  shape). Flattening `dimensions`, `reviews`, and `meta` into tabular
  columns/tables is explicitly deferred to the Transform stage.
- Because DummyJSON's underlying data can change between runs, multiple raw
  snapshots may contain the same `id` with different `price`/`stock`/`rating`
  values. The Transform/Load stages must treat `extracted_at` as part of the
  record's identity if historical tracking is needed, rather than assuming a
  single row per `id`.
- Storage grows by one file per run. Since `data/raw/` is not committed to git,
  retention/cleanup is an operational concern for the runbook, not a version
  control concern.
