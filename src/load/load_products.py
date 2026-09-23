"""Load stage: promote validated processed tables to the output layer.

Copies the normalized CSV tables from data/processed/ to data/output/ and
writes a manifest describing what was loaded. This is the final,
publish-ready layer — see docs/entity-relationship-diagram.md for the schema
and contracts/ for the per-table data contracts.
"""

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from src.utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"

TABLES = ["products", "product_reviews", "product_tags", "product_images"]


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run(config_path: Path = DEFAULT_CONFIG_PATH) -> Path:
    config = load_config(config_path)
    processed_dir = PROJECT_ROOT / config["paths"]["processed_data_dir"]
    output_dir = PROJECT_ROOT / config["paths"]["output_data_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "loaded_at": datetime.now(timezone.utc).isoformat(),
        "tables": {},
    }

    for table in TABLES:
        source_path = processed_dir / f"{table}.csv"
        if not source_path.exists():
            raise FileNotFoundError(
                f"Missing processed table '{table}.csv' — run the Transform stage first"
            )
        dest_path = output_dir / f"{table}.csv"
        shutil.copyfile(source_path, dest_path)

        row_count = len(pd.read_csv(dest_path))
        manifest["tables"][table] = {"row_count": row_count, "file": dest_path.name}
        logger.info("Loaded %d rows into %s", row_count, dest_path)

    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    logger.info("Wrote load manifest to %s", manifest_path)

    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load validated tables from data/processed/ into data/output/"
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to config.yaml"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        output_dir = run(args.config)
    except Exception:
        logger.exception("Load failed")
        sys.exit(1)
    print(f"Load complete: {output_dir}")


if __name__ == "__main__":
    main()
