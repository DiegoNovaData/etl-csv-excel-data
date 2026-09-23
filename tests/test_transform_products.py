import json
from pathlib import Path

import yaml

from src.transform.transform_products import (
    build_images_table,
    build_products_table,
    build_reviews_table,
    build_tags_table,
    find_latest_raw_snapshot,
    run,
)

SAMPLE_PRODUCT = {
    "id": 1,
    "title": "Essence Mascara Lash Princess",
    "description": "A mascara.",
    "category": "beauty",
    "brand": "Essence",
    "sku": "BEA-ESS-001",
    "price": 9.99,
    "discountPercentage": 10.0,
    "rating": 2.56,
    "stock": 99,
    "availabilityStatus": "In Stock",
    "minimumOrderQuantity": 48,
    "weight": 4,
    "dimensions": {"width": 15.14, "height": 13.08, "depth": 22.99},
    "warrantyInformation": "1 week warranty",
    "shippingInformation": "Ships in 3-5 business days",
    "returnPolicy": "No return policy",
    "tags": ["beauty", "mascara"],
    "images": ["https://cdn.example.com/1.webp"],
    "thumbnail": "https://cdn.example.com/thumb.webp",
    "meta": {
        "createdAt": "2025-10-09T14:47:01.588Z",
        "updatedAt": "2026-05-23T11:27:41.868Z",
        "barcode": "5784719087687",
        "qrCode": "https://cdn.example.com/qr.png",
    },
    "reviews": [
        {
            "rating": 3,
            "comment": "Would not recommend!",
            "date": "2025-04-30T09:41:02.053Z",
            "reviewerName": "Eleanor Collins",
            "reviewerEmail": "eleanor.collins@x.dummyjson.com",
        },
        {
            "rating": 5,
            "comment": "Highly impressed!",
            "date": "2025-04-30T09:41:02.053Z",
            "reviewerName": "Lucas Gordon",
            "reviewerEmail": "lucas.gordon@x.dummyjson.com",
        },
    ],
}

SAMPLE_PRODUCT_NO_EXTRAS = {
    "id": 2,
    "title": "Generic Grocery Item",
    "description": "Groceries.",
    "category": "groceries",
    "brand": None,
    "sku": "GRO-002",
    "price": 3.5,
    "discountPercentage": 0.0,
    "rating": 4.0,
    "stock": 10,
    "availabilityStatus": "In Stock",
    "minimumOrderQuantity": 1,
    "weight": 1,
    "dimensions": {"width": 1, "height": 1, "depth": 1},
    "warrantyInformation": "No warranty",
    "shippingInformation": "Ships in 1-2 business days",
    "returnPolicy": "No return policy",
    "tags": [],
    "images": [],
    "thumbnail": "https://cdn.example.com/thumb2.webp",
    "meta": {
        "createdAt": "2025-01-01T00:00:00.000Z",
        "updatedAt": "2025-01-02T00:00:00.000Z",
        "barcode": "0000000000000",
        "qrCode": "https://cdn.example.com/qr2.png",
    },
    "reviews": [],
}


def test_build_products_table_flattens_and_derives_columns():
    df = build_products_table([SAMPLE_PRODUCT], extracted_at="2026-09-21T00:00:00Z")

    row = df.iloc[0]
    assert row["product_id"] == 1
    assert row["width"] == 15.14
    assert row["height"] == 13.08
    assert row["depth"] == 22.99
    assert row["barcode"] == "5784719087687"
    assert row["qr_code_url"] == "https://cdn.example.com/qr.png"
    assert row["source_created_at"] == "2025-10-09T14:47:01.588Z"
    assert row["price_with_discount"] == 8.99  # 9.99 * 0.9
    assert row["review_count"] == 2
    assert row["avg_review_rating"] == 4.0  # mean(3, 5)
    assert row["extracted_at"] == "2026-09-21T00:00:00Z"


def test_build_products_table_handles_missing_reviews_and_brand():
    df = build_products_table([SAMPLE_PRODUCT_NO_EXTRAS], extracted_at="2026-09-21T00:00:00Z")

    row = df.iloc[0]
    assert row["review_count"] == 0
    assert row["avg_review_rating"] is None
    assert row["brand"] is None


def test_build_reviews_table_assigns_surrogate_keys_per_product():
    df = build_reviews_table([SAMPLE_PRODUCT, SAMPLE_PRODUCT_NO_EXTRAS])

    assert list(df["review_id"]) == [1, 2]
    assert list(df["product_id"]) == [1, 1]
    assert df.iloc[0]["reviewer_email"] == "eleanor.collins@x.dummyjson.com"


def test_build_tags_table_one_row_per_tag():
    df = build_tags_table([SAMPLE_PRODUCT, SAMPLE_PRODUCT_NO_EXTRAS])

    assert list(df["product_id"]) == [1, 1]
    assert list(df["tag"]) == ["beauty", "mascara"]


def test_build_images_table_one_row_per_image():
    df = build_images_table([SAMPLE_PRODUCT, SAMPLE_PRODUCT_NO_EXTRAS])

    assert list(df["product_id"]) == [1]
    assert list(df["image_url"]) == ["https://cdn.example.com/1.webp"]


def test_find_latest_raw_snapshot_picks_most_recent_by_name(tmp_path: Path):
    older = tmp_path / "products_raw_20260101T000000Z.json"
    newer = tmp_path / "products_raw_20260921T013540Z.json"
    older.write_text("{}", encoding="utf-8")
    newer.write_text("{}", encoding="utf-8")

    assert find_latest_raw_snapshot(tmp_path) == newer


def test_run_writes_all_tables_to_processed_dir(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()

    snapshot = {
        "extracted_at": "2026-09-21T01:35:40.086437+00:00",
        "source": "https://dummyjson.com/products",
        "record_count": 2,
        "products": [SAMPLE_PRODUCT, SAMPLE_PRODUCT_NO_EXTRAS],
    }
    with open(raw_dir / "products_raw_20260921T013540Z.json", "w", encoding="utf-8") as f:
        json.dump(snapshot, f)

    config = {
        "paths": {
            "raw_data_dir": str(raw_dir),
            "processed_data_dir": str(processed_dir),
            "output_data_dir": str(tmp_path / "output"),
        }
    }
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f)

    tables = run(config_path)

    assert set(tables) == {"products", "product_reviews", "product_tags", "product_images"}
    assert (processed_dir / "products.csv").exists()
    assert (processed_dir / "product_reviews.csv").exists()
    assert (processed_dir / "product_tags.csv").exists()
    assert (processed_dir / "product_images.csv").exists()
    assert len(tables["products"]) == 2
