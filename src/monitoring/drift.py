from __future__ import annotations

import pandas as pd

from .psi import calculate_psi


def calculate_feature_drift(
    reference: pd.DataFrame,
    current: pd.DataFrame,
) -> pd.DataFrame:
    results: list[dict[str, float | str]] = []

    common_columns = reference.columns.intersection(current.columns)

    for column in common_columns:
        if not (
            pd.api.types.is_numeric_dtype(reference[column])
            and pd.api.types.is_numeric_dtype(current[column])
        ):
            continue

        psi = calculate_psi(
            reference[column],
            current[column],
        )

        results.append(
            {
                "feature": column,
                "psi": psi,
                "severity": (
                    "stable"
                    if psi < 0.10
                    else "moderate"
                    if psi <= 0.25
                    else "severe"
                ),
            }
        )

    return pd.DataFrame(results)