"""Extract the retail product catalog from the DummyJSON public API.

Source: https://dummyjson.com/docs/products
Output: a timestamped, immutable JSON snapshot under ``data/raw/``.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

from src.utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_with_retries(
    url: str, params: dict, timeout: int, max_retries: int
) -> requests.Response:
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_exc = exc
            wait = 2**attempt
            logger.warning(
                "Request failed (attempt %d/%d): %s. Retrying in %ds",
                attempt,
                max_retries,
                exc,
                wait,
            )
            if attempt < max_retries:
                time.sleep(wait)
    raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts") from last_exc


def fetch_products(
    base_url: str, endpoint: str, page_limit: int, timeout: int, max_retries: int
) -> list:
    """Fetch all products from the paginated DummyJSON endpoint."""
    products: list = []
    skip = 0
    total = None
    url = f"{base_url}{endpoint}"

    while total is None or skip < total:
        params = {"limit": page_limit, "skip": skip}
        response = _get_with_retries(url, params, timeout, max_retries)
        payload = response.json()
        products.extend(payload["products"])
        total = payload["total"]
        skip += page_limit
        logger.info("Fetched %d/%d products", min(skip, total), total)

    return products


def save_raw(products: list, output_dir: Path, source_url: str) -> Path:
    """Persist the raw extract as a timestamped JSON snapshot."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"products_raw_{timestamp}.json"

    payload = {
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "source": source_url,
        "record_count": len(products),
        "products": products,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info("Saved %d records to %s", len(products), output_path)
    return output_path


def run(config_path: Path = DEFAULT_CONFIG_PATH) -> Path:
    config = load_config(config_path)
    source_cfg = config["source"]
    output_dir = PROJECT_ROOT / config["paths"]["raw_data_dir"]

    products = fetch_products(
        base_url=source_cfg["base_url"],
        endpoint=source_cfg["endpoint"],
        page_limit=source_cfg["page_limit"],
        timeout=source_cfg["timeout_seconds"],
        max_retries=source_cfg["max_retries"],
    )
    source_url = f"{source_cfg['base_url']}{source_cfg['endpoint']}"
    return save_raw(products, output_dir, source_url)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract the retail product catalog from the DummyJSON API"
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to config.yaml"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        output_path = run(args.config)
    except Exception:
        logger.exception("Extraction failed")
        sys.exit(1)
    print(f"Extraction complete: {output_path}")


if __name__ == "__main__":
    main()
