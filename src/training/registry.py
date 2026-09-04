"""
Promote the best training candidate to Production.

Usage:
    python -m src.training.registry --experiment skye8-credit-risk \
        --model-name skye8-credit-risk-model --metric pr_auc

This queries every run in the given MLflow experiment, ranks them by the
chosen metric, and transitions the corresponding registered model
version to the "Production" stage -- archiving whatever was Production
before. The decision (which run, which metric value, when, by whom) is
printed and should be copied into docs/model_card.md as the recorded
promotion decision the brief requires.

Why pr_auc by default: about 1 in 5 loans default, so precision-recall
AUC reflects ranking quality on the minority (defaulting) class more
directly than ROC-AUC, which is optimistic under imbalance. Brier score
(calibration) is reported alongside as a tie-breaker consideration,
since the API returns a probability the credit committee will read at
face value, not just a rank.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

import mlflow
from mlflow.tracking import MlflowClient

MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"


def find_best_run(client: MlflowClient, experiment_name: str, metric: str) -> mlflow.entities.Run:
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        raise ValueError(f"no such experiment: {experiment_name}")

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=[f"metrics.{metric} DESC"],
        max_results=1,
    )
    if not runs:
        raise ValueError(f"no runs found in experiment {experiment_name}")
    return runs[0]


def find_model_version_for_run(client: MlflowClient, model_name: str, run_id: str):
    for version in client.search_model_versions(f"name='{model_name}'"):
        if version.run_id == run_id:
            return version
    raise ValueError(f"no registered version of {model_name} found for run {run_id}")


def promote(experiment_name: str, model_name: str, metric: str) -> dict:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    best_run = find_best_run(client, experiment_name, metric)
    version = find_model_version_for_run(client, model_name, best_run.info.run_id)

    client.transition_model_version_stage(
        name=model_name,
        version=version.version,
        stage="Production",
        archive_existing_versions=True,
    )
    # Also set the modern alias-based pointer (MLflow is deprecating
    # stages in favour of aliases) so "which model is live" can be
    # queried either way: get_model_version_by_alias(name, "production").
    client.set_registered_model_alias(name=model_name, alias="production", version=version.version)
    client.set_model_version_tag(
        name=model_name,
        version=version.version,
        key="promotion_metric",
        value=f"{metric}={best_run.data.metrics.get(metric):.4f}",
    )

    decision = {
        "promoted_at_utc": datetime.now(UTC).isoformat(),
        "model_name": model_name,
        "promoted_version": version.version,
        "run_id": best_run.info.run_id,
        "run_name": best_run.data.tags.get("mlflow.runName", "unknown"),
        "selection_metric": metric,
        "selection_metric_value": best_run.data.metrics.get(metric),
        "all_metrics": dict(best_run.data.metrics),
        "git_commit": best_run.data.tags.get("git_commit"),
        "data_version": best_run.data.tags.get("data_version"),
    }
    return decision


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", default="skye8-credit-risk")
    parser.add_argument("--model-name", default="skye8-credit-risk-model")
    parser.add_argument("--metric", default="pr_auc")
    args = parser.parse_args()

    decision = promote(args.experiment, args.model_name, args.metric)
    print("[promotion decision]")
    for key, value in decision.items():
        print(f"  {key}: {value}")
