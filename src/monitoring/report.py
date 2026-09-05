from __future__ import annotations

import pandas as pd

from src.monitoring.drift import calculate_feature_drift


def generate_monitoring_report(
    reference_data: pd.DataFrame,
    production_data: pd.DataFrame,
) -> pd.DataFrame:
    """Generate a feature-drift monitoring report."""

    drift_report = calculate_feature_drift(
        reference_data,
        production_data,
    )

    return drift_report


def save_monitoring_report(
    report: pd.DataFrame,
    output_path: str,
) -> None:
    """Save a monitoring report as a CSV file."""

    report.to_csv(output_path, index=False)
