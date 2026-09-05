import pandas as pd

from src.monitoring.drift import calculate_feature_drift


def test_feature_drift_returns_results():
    reference = pd.DataFrame({"age": [20, 21, 22, 23, 24], "income": [100, 110, 120, 130, 140]})

    current = pd.DataFrame(
        {
            "age": [20, 21, 22, 23, 24],
            "income": [500, 510, 520, 530, 540],
        }
    )

    result = calculate_feature_drift(reference, current)

    assert "feature" in result.columns
    assert "psi" in result.columns
    assert "severity" in result.columns
    assert len(result) == 2
