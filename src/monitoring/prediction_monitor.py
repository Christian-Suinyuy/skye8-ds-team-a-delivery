from __future__ import annotations

from collections import Counter
from typing import Sequence


def prediction_distribution(
    predictions: Sequence,
) -> dict:
    if not predictions:
        raise ValueError("Predictions cannot be empty.")

    counts = Counter(predictions)
    total = len(predictions)

    return {
        label: count / total
        for label, count in counts.items()
    }