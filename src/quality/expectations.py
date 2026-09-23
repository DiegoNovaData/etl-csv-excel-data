"""Lightweight, in-code Great Expectations checks for the Transform stage.

Uses GX's ephemeral (in-memory) context — no `great_expectations init`
project scaffolding is created or committed. See
docs/adr/0005-data-quality-great-expectations.md for why.
"""

import pandas as pd
import great_expectations as gx
from great_expectations import expectations as gxe

from src.utils.logger import get_logger

logger = get_logger(__name__)

CRITICAL_SUITE_NAME = "products_critical"
WARNING_SUITE_NAME = "products_warning"


class QualityCheckFailed(RuntimeError):
    """Raised when a critical expectation suite fails validation."""


def _validate(df: pd.DataFrame, suite_name: str, expectations: list):
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas("in_memory")
    data_asset = data_source.add_dataframe_asset(name=suite_name)
    batch_definition = data_asset.add_batch_definition_whole_dataframe(f"{suite_name}_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    suite = context.suites.add(gx.ExpectationSuite(name=suite_name))
    for expectation in expectations:
        suite.add_expectation(expectation)

    return batch.validate(suite)


def _log_result(level: str, result) -> None:
    if result.success:
        logger.info("Quality suite (%s) passed: %d expectations", level, len(result.results))
        return
    for r in result.results:
        if not r.success:
            logger.warning(
                "Quality check failed [%s] %s on column=%s",
                level,
                r.expectation_config.type,
                r.expectation_config.kwargs.get("column"),
            )


def validate_products(df: pd.DataFrame) -> None:
    """Validate the products table before it is written to data/processed/.

    Critical expectations raise ``QualityCheckFailed`` and must abort the
    Transform run. Warning expectations are logged but do not stop it —
    they reflect known source data quirks (see docs/data-dictionary.md)
    rather than structural problems.
    """
    critical_result = _validate(
        df,
        CRITICAL_SUITE_NAME,
        [
            gxe.ExpectColumnValuesToNotBeNull(column="product_id"),
            gxe.ExpectColumnValuesToBeUnique(column="product_id"),
            gxe.ExpectColumnValuesToNotBeNull(column="title"),
            gxe.ExpectColumnValuesToNotBeNull(column="price"),
            gxe.ExpectColumnValuesToBeBetween(column="price", min_value=0),
        ],
    )
    _log_result("critical", critical_result)
    if not critical_result.success:
        failed = [r.expectation_config.type for r in critical_result.results if not r.success]
        raise QualityCheckFailed(f"Critical data quality checks failed: {failed}")

    warning_result = _validate(
        df,
        WARNING_SUITE_NAME,
        [
            gxe.ExpectColumnValuesToBeBetween(column="rating", min_value=0, max_value=5),
            gxe.ExpectColumnValuesToBeBetween(column="discount_percentage", min_value=0, max_value=100),
            gxe.ExpectColumnValuesToBeBetween(column="stock", min_value=0),
            gxe.ExpectColumnValuesToNotBeNull(column="brand", mostly=0.8),
        ],
    )
    _log_result("warning", warning_result)
