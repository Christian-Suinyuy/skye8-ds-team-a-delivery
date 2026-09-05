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
        # Numeric features use the standard PSI calculation.
        if pd.api.types.is_numeric_dtype(reference[column]) and pd.api.types.is_numeric_dtype(
            current[column]
        ):
            psi = calculate_psi(reference[column], current[column])

        # Categorical features use category proportions.
        else:
            ref_dist = reference[column].astype(str).value_counts(normalize=True)
            cur_dist = current[column].astype(str).value_counts(normalize=True)

            categories = ref_dist.index.union(cur_dist.index)
            ref_dist = ref_dist.reindex(categories, fill_value=0.0001).clip(lower=0.0001)
            cur_dist = cur_dist.reindex(categories, fill_value=0.0001).clip(lower=0.0001)

            psi = float(
                ((cur_dist - ref_dist) * (cur_dist / ref_dist).map(__import__("math").log)).sum()
            )

        results.append(
            {
                "feature": column,
                "psi": psi,
                "severity": ("stable" if psi < 0.10 else "moderate" if psi <= 0.25 else "severe"),
            }
        )

    return pd.DataFrame(results)
