# Runbook: Extract stage (DummyJSON products)

## Purpose
Pull the full retail product catalog from the DummyJSON public API and store
it as a raw JSON snapshot for downstream processing.

Related: [ADR 0002 - Data source selection](../adr/0002-data-source-selection.md),
[ADR 0003 - Raw data storage format](../adr/0003-raw-data-storage-format.md).

## Prerequisites
- Python 3.10+
- Dependencies installed: `pip install -r requirements.txt`
- Outbound internet access to `https://dummyjson.com` (no API key required)

## Running the extraction

```bash
python -m src.extract.extract_dummyjson
```

Optional: point to a different config file (e.g. for testing against a
different `page_limit` or output path):

```bash
python -m src.extract.extract_dummyjson --config path/to/other_config.yaml
```

## Expected output
- A new file at `data/raw/products_raw_<UTC_TIMESTAMP>.json`, e.g.
  `products_raw_20260921T013540Z.json`.
- Console output ending with `Extraction complete: <path>`.
- Log entries appended to `logs/etl.log`, one line per page fetched plus a
  final "Saved N records to <path>" line.

## Verifying success
1. Check the process exit code is `0`.
2. Confirm a new file exists in `data/raw/` with `record_count` matching the
   `total` reported by the API (currently 194 products).
3. Spot-check `logs/etl.log` for `WARNING`/`ERROR` entries during the run.

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `RuntimeError: Failed to fetch ... after N attempts` | Network outage, DNS issue, or DummyJSON downtime | Check connectivity to `https://dummyjson.com/products`; re-run once the source is reachable. The script already retries with exponential backoff (`max_retries` in `config/config.yaml`). |
| HTTP 429 (rate limited) | Too many requests in a short window | Increase `timeout_seconds`/reduce request frequency; avoid running the script in a tight loop. |
| `record_count` differs from `total` in previous runs | Source dataset changed between runs (expected — see [ADR 0002](../adr/0002-data-source-selection.md)) | Not an error. Each raw file is an independent point-in-time snapshot. |
| `FileNotFoundError` for `config/config.yaml` | Script run from the wrong working directory or with a bad `--config` path | Run from the project root, or pass an absolute `--config` path. |

## Rollback
Raw snapshots are immutable and independent — if a run produced a bad or
partial file (e.g. process killed mid-write), simply delete that file from
`data/raw/` and re-run the extraction. No other file depends on a specific
snapshot name.

## Scheduling (optional)
This stage is safe to run repeatedly (idempotent per run — it always writes a
new, uniquely named file). To schedule it:

- **Windows Task Scheduler**: create a task that runs
  `python -m src.extract.extract_dummyjson` with the working directory set to
  the project root.
- **cron (Linux/macOS)**:
  ```
  0 * * * * cd /path/to/etl-csv-excel-data && /path/to/venv/bin/python -m src.extract.extract_dummyjson >> logs/cron.log 2>&1
  ```

## Retention
`data/raw/` is git-ignored and grows by one file per run. Periodically archive
or delete old snapshots according to your own storage policy; there is no
automated cleanup in this stage.
