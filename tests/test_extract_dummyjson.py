import json
from pathlib import Path

import pytest

from src.extract.extract_dummyjson import fetch_products, save_raw


def _page(products, total, skip, limit):
    return {"products": products, "total": total, "skip": skip, "limit": limit}


def test_fetch_products_paginates_until_total_reached(requests_mock):
    base_url = "https://dummyjson.com"
    endpoint = "/products"
    url = f"{base_url}{endpoint}"

    page_1 = [{"id": 1, "title": "Product 1"}, {"id": 2, "title": "Product 2"}]
    page_2 = [{"id": 3, "title": "Product 3"}]

    requests_mock.get(
        url,
        [
            {"json": _page(page_1, total=3, skip=0, limit=2)},
            {"json": _page(page_2, total=3, skip=2, limit=2)},
        ],
    )

    products = fetch_products(
        base_url=base_url, endpoint=endpoint, page_limit=2, timeout=5, max_retries=1
    )

    assert [p["id"] for p in products] == [1, 2, 3]
    assert requests_mock.call_count == 2


def test_fetch_products_retries_on_transient_error(requests_mock):
    base_url = "https://dummyjson.com"
    endpoint = "/products"
    url = f"{base_url}{endpoint}"

    requests_mock.get(
        url,
        [
            {"status_code": 500},
            {"json": _page([{"id": 1, "title": "Product 1"}], total=1, skip=0, limit=1)},
        ],
    )

    products = fetch_products(
        base_url=base_url, endpoint=endpoint, page_limit=1, timeout=5, max_retries=2
    )

    assert len(products) == 1
    assert requests_mock.call_count == 2


def test_save_raw_writes_expected_structure(tmp_path: Path):
    products = [{"id": 1, "title": "Product 1"}]
    source_url = "https://dummyjson.com/products"

    output_path = save_raw(products, tmp_path, source_url)

    assert output_path.exists()
    assert output_path.parent == tmp_path

    with open(output_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    assert payload["source"] == source_url
    assert payload["record_count"] == 1
    assert payload["products"] == products
    assert "extracted_at" in payload
