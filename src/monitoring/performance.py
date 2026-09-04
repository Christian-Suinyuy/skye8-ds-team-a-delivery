from __future__ import annotations

from typing import Sequence

from sklearn.metrics import (
  accuracy_score,
  f1_score,
  precision_score,
  recall_score,
)

def calculate_performance(
    y_true: Sequence,
    y_pred: Sequence,
) -> dict[str, float]:
  return {
    "accuracy": float(accuracy_score(y_true, y_pred)),
    "precision": float(
      precision_score,(
        y_true,
        y_pred,
        average="weighted",
        zero_division =0
      )
    ),
    "recall": float(
      recall_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
      )
    ),
    "f1": float(
      f1_score(
        y_true,
        y_pred,
        average = "weighted",
        zero_division = 0,
      )
    ),
  }