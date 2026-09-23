# Runbook: Load stage

## Purpose
Promote the validated tables in `data/processed/` to `data/output/` as the
final, publish-ready CSV deliverables, plus a `manifest.json` describing what
was loaded.

Related: [docs/entity-relationship-diagram.md](../entity-relationship-diagram.md),
[`contracts/`](../../contracts/).

## Prerequisites
- `data/processed/*.csv` exist (run the
  [Transform runbook](transform-runbook.md) first).

## Running the load
```bash
python -m src.load.load_products
```

## Expected output
- `data/output/products.csv`, `product_reviews.csv`, `product_tags.csv`,
  `product_images.csv`
- `data/output/manifest.json` with `loaded_at` and per-table row counts
- Console output: `Load complete: <path>`

## Verifying success
1. Exit code `0`.
2. Row counts in `manifest.json` match the row counts logged by the
   Transform stage for the same run.

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `FileNotFoundError: Missing processed table '<table>.csv'` | Transform stage didn't run, or exited before writing that table | Run the [Transform runbook](transform-runbook.md) first and confirm it exited 0. |

## Rollback
`data/output/*.csv` and `manifest.json` are overwritten on every run. To
revert to a previous deliverable, re-run Transform against an older raw
snapshot before re-running Load.
