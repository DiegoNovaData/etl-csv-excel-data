# 0005. Data quality validation with Great Expectations (lightweight, in-code)

## Status
Accepted

## Context
The Transform stage needs automated data quality checks before writing
`data/processed/*.csv`, so bad data doesn't silently reach the Load layer.
[Great Expectations](https://greatexpectations.io) (GX) is a widely used,
recognizable tool for this. Its default workflow (`great_expectations init`)
scaffolds a `gx/` project directory (datasources, checkpoints, Data Docs
config) — useful for larger, long-lived data platforms, but heavy for a
single-pipeline portfolio repo.

## Decision
Use GX's in-code "ephemeral" API (`gx.get_context(mode="ephemeral")`, a
fluent Pandas datasource, and an `ExpectationSuite` built directly in Python)
inside [`src/quality/expectations.py`](../../src/quality/expectations.py),
with no `gx/` project folder committed to the repo.

Expectations are split into two severities:
- **Critical** (first suite in `validate_products`): `product_id` non-null
  and unique, `title` non-null, `price` non-null and >= 0. Failure raises
  `QualityCheckFailed`, which aborts the Transform run **before** anything
  is written to `data/processed/`.
- **Warning** (second suite): `rating` in [0, 5], `discount_percentage` in
  [0, 100], `stock` >= 0, `brand` mostly non-null (>= 80%). Failures are
  logged but do not stop the pipeline, since these reflect known source data
  quirks (see [docs/data-dictionary.md](../data-dictionary.md)) rather than
  structural problems — confirmed in practice: the `brand` warning fires on
  every real run because DummyJSON genuinely omits `brand` for categories
  like groceries.

## Consequences
- No GX Data Docs HTML site is generated; validation results are surfaced
  through the application's own logging (`logs/etl.log`), not GX's reporting
  UI. Acceptable given the repo's current scale; revisit if more
  datasets/suites are added and a shared, browsable validation history
  becomes worth the added complexity.
- Expectation suites live only in memory during a run (ephemeral context) —
  they are not persisted/versioned in a GX store. The suite definitions in
  `src/quality/expectations.py` are themselves the versioned artifact (via
  git), which keeps `great_expectations`'s footprint in this repo to a
  single module plus its dependency.
- The critical/warning split is a manual convention enforced by how
  `validate_products` is written, not a built-in GX concept — it must be
  kept in mind when adding new expectations (decide which suite they belong
  in).
