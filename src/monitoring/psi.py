from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_psi(
    reference: pd.Series,
    current: pd.Series,
    bins: int = 10,
) -> float:
    """Calculate PSI between a reference and current distribution."""
    reference = pd.to_numeric(reference, errors="coerce").dropna()
    current = pd.to_numeric(current, errors="coerce").dropna()

    if reference.empty or current.empty:
        raise ValueError("Reference and current data must not be empty.")

    if reference.min() == reference.max():
        return 0.0

    edges = np.linspace(
        reference.min(),
        reference.max(),
        bins + 1,
    )

    edges[0] = -np.inf
    edges[-1] = np.inf

    reference_bins = pd.cut(
        reference,
        bins=edges,
        include_lowest=True,
    )

    current_bins = pd.cut(
        current,
        bins=edges,
        include_lowest=True,
    )

    reference_dist = reference_bins.value_counts(
        normalize=True,
        sort=False,
    )

    current_dist = current_bins.value_counts(
        normalize=True,
        sort=False,
    )

    reference_dist = reference_dist.clip(lower=0.0001)
    current_dist = current_dist.clip(lower=0.0001)

    psi = (
        (current_dist - reference_dist)
        * np.log(current_dist / reference_dist)
    ).sum()

    return float(psi)