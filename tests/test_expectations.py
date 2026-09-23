import pandas as pd
import pytest

from src.quality.expectations import QualityCheckFailed, validate_products

VALID_PRODUCTS = pd.DataFrame(
    [
        {
            "product_id": 1,
            "title": "Product 1",
            "price": 9.99,
            "rating": 4.5,
            "discount_percentage": 10.0,
            "stock": 5,
            "brand": "Acme",
        },
        {
            "product_id": 2,
            "title": "Product 2",
            "price": 19.99,
            "rating": 3.0,
            "discount_percentage": 0.0,
            "stock": 0,
            "brand": "Acme",
        },
    ]
)


def test_validate_products_passes_on_clean_data():
    validate_products(VALID_PRODUCTS.copy())  # should not raise


def test_validate_products_raises_on_duplicate_product_id():
    df = VALID_PRODUCTS.copy()
    df.loc[1, "product_id"] = 1  # duplicate id -> critical failure

    with pytest.raises(QualityCheckFailed):
        validate_products(df)


def test_validate_products_raises_on_negative_price():
    df = VALID_PRODUCTS.copy()
    df.loc[0, "price"] = -5.0

    with pytest.raises(QualityCheckFailed):
        validate_products(df)


def test_validate_products_does_not_raise_on_warning_level_issue():
    df = VALID_PRODUCTS.copy()
    df.loc[0, "rating"] = 7.0  # out of [0, 5] range -> warning only, not critical

    validate_products(df)  # should not raise despite the out-of-range rating
