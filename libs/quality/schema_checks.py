"""Schema validation checks using Polars DataFrames."""
from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from libs.common.exceptions import SchemaValidationError


@dataclass
class SchemaCheckResult:
    passed: bool
    missing_cols: list[str]
    type_mismatches: dict[str, tuple[str, str]]  # col -> (expected, actual)


def check_schema(df: pl.DataFrame, expected: dict[str, str]) -> SchemaCheckResult:
    """Validate that *df* contains all expected columns with compatible dtypes.

    Args:
        df: The DataFrame to validate.
        expected: Mapping of column name to expected Polars dtype string
                  (e.g. ``{"close": "Float64", "volume": "Int64"}``).

    Returns:
        A :class:`SchemaCheckResult` describing any violations.
    """
    actual = {name: str(dtype) for name, dtype in zip(df.columns, df.dtypes)}
    missing = [col for col in expected if col not in actual]
    mismatches = {
        col: (expected[col], actual[col])
        for col in expected
        if col in actual and actual[col] != expected[col]
    }
    return SchemaCheckResult(
        passed=not missing and not mismatches,
        missing_cols=missing,
        type_mismatches=mismatches,
    )


def assert_schema(df: pl.DataFrame, expected: dict[str, str]) -> None:
    """Like :func:`check_schema` but raises on failure."""
    result = check_schema(df, expected)
    if not result.passed:
        raise SchemaValidationError(
            f"Schema check failed — missing: {result.missing_cols}, "
            f"type mismatches: {result.type_mismatches}"
        )
