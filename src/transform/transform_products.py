"""Transform the latest raw DummyJSON snapshot into normalized CSV tables.

Reads the most recent snapshot from data/raw/, flattens nested fields,
computes derived columns, validates the result with the Great Expectations
suites in src/quality/expectations.py, and writes four tables to
data/processed/ matching docs/entity-relationship-diagram.md:

    products.csv         - one row per product (current-state grain)
    product_reviews.csv  - one row per review
    product_tags.csv     - one row per (product, tag)
    product_images.csv   - one row per (product, image)
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

from src.quality.expectations import QualityCheckFailed, validate_products
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_latest_raw_snapshot(raw_dir: Path) -> Path:
    snapshots = sorted(raw_dir.glob("products_raw_*.json"))
    if not snapshots:
        raise FileNotFoundError(f"No raw snapshots found in {raw_dir}")
    return snapshots[-1]


def load_raw_snapshot(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _price_with_discount(price, discount_percentage):
    if price is None or discount_percentage is None:
        return None
    return round(price * (1 - discount_percentage / 100), 2)


def build_products_table(raw_products: list, extracted_at: str) -> pd.DataFrame:
    rows = []
    for p in raw_products:
        dimensions = p.get("dimensions") or {}
        meta = p.get("meta") or {}
        reviews = p.get("reviews") or []
        review_ratings = [r["rating"] for r in reviews if r.get("rating") is not None]

        rows.append(
            {
                "product_id": p["id"],
                "title": p.get("title"),
                "description": p.get("description"),
                "category": p.get("category"),
                "brand": p.get("brand"),
                "sku": p.get("sku"),
                "price": p.get("price"),
                "discount_percentage": p.get("discountPercentage"),
                "price_with_discount": _price_with_discount(
                    p.get("price"), p.get("discountPercentage")
                ),
                "rating": p.get("rating"),
                "stock": p.get("stock"),
                "availability_status": p.get("availabilityStatus"),
                "minimum_order_quantity": p.get("minimumOrderQuantity"),
                "weight": p.get("weight"),
                "width": dimensions.get("width"),
                "height": dimensions.get("height"),
                "depth": dimensions.get("depth"),
                "warranty_information": p.get("warrantyInformation"),
                "shipping_information": p.get("shippingInformation"),
                "return_policy": p.get("returnPolicy"),
                "barcode": meta.get("barcode"),
                "qr_code_url": meta.get("qrCode"),
                "thumbnail_url": p.get("thumbnail"),
                "source_created_at": meta.get("createdAt"),
                "source_updated_at": meta.get("updatedAt"),
                "review_count": len(reviews),
                "avg_review_rating": (
                    round(sum(review_ratings) / len(review_ratings), 2)
                    if review_ratings
                    else None
                ),
                "extracted_at": extracted_at,
            }
        )
    return pd.DataFrame(rows)


def build_reviews_table(raw_products: list) -> pd.DataFrame:
    rows = []
    review_id = 1
    for p in raw_products:
        for r in p.get("reviews") or []:
            rows.append(
                {
                    "review_id": review_id,
                    "product_id": p["id"],
                    "rating": r.get("rating"),
                    "comment": r.get("comment"),
                    "review_date": r.get("date"),
                    "reviewer_name": r.get("reviewerName"),
                    "reviewer_email": r.get("reviewerEmail"),
                }
            )
            review_id += 1
    return pd.DataFrame(rows)


def build_tags_table(raw_products: list) -> pd.DataFrame:
    rows = [
        {"product_id": p["id"], "tag": tag}
        for p in raw_products
        for tag in (p.get("tags") or [])
    ]
    return pd.DataFrame(rows)


def build_images_table(raw_products: list) -> pd.DataFrame:
    rows = [
        {"product_id": p["id"], "image_url": url}
        for p in raw_products
        for url in (p.get("images") or [])
    ]
    return pd.DataFrame(rows)


def write_tables(tables: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        path = output_dir / f"{name}.csv"
        df.to_csv(path, index=False)
        logger.info("Wrote %d rows to %s", len(df), path)


def run(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    config = load_config(config_path)
    raw_dir = PROJECT_ROOT / config["paths"]["raw_data_dir"]
    processed_dir = PROJECT_ROOT / config["paths"]["processed_data_dir"]

    snapshot_path = find_latest_raw_snapshot(raw_dir)
    logger.info("Using raw snapshot: %s", snapshot_path)
    snapshot = load_raw_snapshot(snapshot_path)
    raw_products = snapshot["products"]
    extracted_at = snapshot["extracted_at"]

    tables = {
        "products": build_products_table(raw_products, extracted_at),
        "product_reviews": build_reviews_table(raw_products),
        "product_tags": build_tags_table(raw_products),
        "product_images": build_images_table(raw_products),
    }

    validate_products(tables["products"])

    write_tables(tables, processed_dir)
    return tables


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform the latest raw product snapshot into tabular CSVs"
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to config.yaml"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        tables = run(args.config)
    except QualityCheckFailed as exc:
        logger.error("Transform aborted: %s", exc)
        sys.exit(1)
    except Exception:
        logger.exception("Transform failed")
        sys.exit(1)
    total_rows = sum(len(df) for df in tables.values())
    print(f"Transform complete: {total_rows} rows across {len(tables)} tables")


if __name__ == "__main__":
    main()
