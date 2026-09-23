# Runbook: Transform stage

## Purpose
Turn the latest raw snapshot (`data/raw/products_raw_*.json`) into four
normalized, validated CSV tables in `data/processed/`, matching the schema in
[docs/entity-relationship-diagram.md](../entity-relationship-diagram.md).

Related: [ADR 0004 - Data contracts](../adr/0004-data-contracts-approach.md),
[ADR 0005 - Data quality with Great Expectations](../adr/0005-data-quality-great-expectations.md).

## Prerequisites
- At least one raw snapshot exists in `data/raw/` (run the
  [Extract runbook](extract-runbook.md) first).
- Dependencies installed: `pip install -r requirements-dev.txt`

## Running the transformation
```bash
python -m src.transform.transform_products
```

## Expected output
- `data/processed/products.csv`
- `data/processed/product_reviews.csv`
- `data/processed/product_tags.csv`
- `data/processed/product_images.csv`
- Console output: `Transform complete: N rows across 4 tables`
- Log entries in `logs/etl.log`: which raw snapshot was used, and the result
  of each Great Expectations suite (`critical`/`warning`).

## Verifying success
1. Exit code `0`.
2. `products.csv` row count matches the `record_count` of the raw snapshot
   used (see the "Using raw snapshot" log line, then that file's
   `record_count` field).
3. No `Quality check failed [critical]` lines in `logs/etl.log`.

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `FileNotFoundError: No raw snapshots found` | Extract stage never ran, or `data/raw/` was cleaned | Run the [Extract runbook](extract-runbook.md) first. |
| Process exits 1 with `QualityCheckFailed` | A critical expectation failed (null/duplicate `product_id`, null `title`, null or negative `price`) | Inspect the raw snapshot named in the preceding log line — this indicates a real upstream data quality issue, not something to silently bypass. |
| `Quality check failed [warning] ... column=brand` in logs, process still exits 0 | Expected — DummyJSON omits `brand` for some categories (e.g. groceries); see [docs/data-dictionary.md](../data-dictionary.md) | No action needed unless the warning rate changes unexpectedly. |

## Rollback
`data/processed/*.csv` is fully regenerated (overwritten, not appended) on
every run. If a run produced bad output, fix the input or the transform
logic and re-run — there is no partial state to roll back.
