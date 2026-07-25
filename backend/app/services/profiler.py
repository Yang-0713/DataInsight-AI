import math
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)


def _safe_number(value: Any) -> float | int | None:
    if pd.isna(value):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    if number.is_integer():
        return int(number)
    return round(number, 6)


def _column_type(series: pd.Series) -> str:
    if is_bool_dtype(series):
        return "boolean"
    if is_numeric_dtype(series):
        return "numeric"
    if is_datetime64_any_dtype(series):
        return "datetime"

    values = series.dropna()
    if not values.empty:
        parsed = pd.to_datetime(values, errors="coerce", format="mixed")
        if float(parsed.notna().mean()) >= 0.8:
            return "datetime"
    return "categorical"


def build_profile(frame: pd.DataFrame) -> dict[str, Any]:
    row_count, column_count = frame.shape
    missing_cells = int(frame.isna().sum().sum())
    total_cells = row_count * column_count
    columns: list[dict[str, Any]] = []

    for name in frame.columns:
        series = frame[name]
        missing_count = int(series.isna().sum())
        columns.append(
            {
                "name": str(name),
                "data_type": _column_type(series),
                "pandas_type": str(series.dtype),
                "missing_count": missing_count,
                "missing_percentage": round(
                    missing_count / row_count * 100, 2
                )
                if row_count
                else 0.0,
                "unique_count": int(series.nunique(dropna=True)),
            }
        )

    return {
        "rows": int(row_count),
        "columns": int(column_count),
        "duplicate_rows": int(frame.duplicated().sum()),
        "missing_cells": missing_cells,
        "missing_percentage": round(missing_cells / total_cells * 100, 2)
        if total_cells
        else 0.0,
        "column_profiles": columns,
    }


def build_statistics(frame: pd.DataFrame) -> dict[str, Any]:
    numerical: list[dict[str, Any]] = []
    categorical: list[dict[str, Any]] = []

    for name in frame.columns:
        series = frame[name]
        if is_numeric_dtype(series) and not is_bool_dtype(series):
            numeric = pd.to_numeric(series, errors="coerce")
            numeric = numeric[np.isfinite(numeric)]
            numerical.append(
                {
                    "column": str(name),
                    "count": int(numeric.count()),
                    "mean": _safe_number(numeric.mean()),
                    "median": _safe_number(numeric.median()),
                    "std": _safe_number(numeric.std()),
                    "min": _safe_number(numeric.min()),
                    "q1": _safe_number(numeric.quantile(0.25)),
                    "q3": _safe_number(numeric.quantile(0.75)),
                    "max": _safe_number(numeric.max()),
                }
            )
            continue

        values = series.dropna().astype(str)
        counts = values.value_counts().head(10)
        non_null_count = int(values.count())
        distribution = [
            {
                "value": str(value),
                "count": int(count),
                "percentage": round(int(count) / non_null_count * 100, 2)
                if non_null_count
                else 0.0,
            }
            for value, count in counts.items()
        ]
        categorical.append(
            {
                "column": str(name),
                "count": non_null_count,
                "unique": int(values.nunique()),
                "top": distribution[0]["value"] if distribution else None,
                "frequency": distribution[0]["count"] if distribution else 0,
                "distribution": distribution,
            }
        )

    return {"numerical": numerical, "categorical": categorical}
